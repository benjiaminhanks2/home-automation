import sys
from logging import RootLogger
from typing import Callable
import logging

from communication.DeviceLifetimeManager import DeviceLifetimeManager
from communication.IncommingZwaveCommunicationThread import IncommingZwaveCommunicationThread
from communication.SensorsPollingThread import SensorsPollingThread
from communication.TextSensorDataParser import TextSensorDataParser
from communication.WemoSwitch import WemoSwitch
from communication.ZWaveDevice import ZWaveDevice
from communication.actuator.ActuatorCommands import ActuatorCommands
from communication.actuator.ActuatorStrategies import ActuatorStrategies
from communication.actuator.AsyncActuatorCommands import AsyncActuatorCommands
from communication.actuator.strategies.GroupStrategy import GroupStrategy
from communication.actuator.strategies.SerialSendStrategy import SerialSendStrategy
from communication.actuator.strategies.WemoSwitchStrategy import WemoSwitchStrategy
from communication.actuator.strategies.ZWaveStrategy import ZWaveStrategy
from communication.encriptors.AesEncriptor import AesEncriptor
from communication.Serial import Serial
from communication.SerialBluetooth import SerialBluetooth
from config import general
from event.ChangeActuatorRequestEvent import ChangeActuatorRequestEvent
from event.SensorUpdateEvent import SensorUpdateEvent
from ifttt.ExpressionValidator import ExpressionValidator
from ifttt.command.CommandExecutor import CommandExecutor
from ifttt.command.TextCommunicationEnhancer import TextCommunicationEnhancer
from ifttt.parser.ActuatorStateTokenConverter import ActuatorStateTokenConverter
from ifttt.parser.ActuatorTokenConverter import ActuatorTokenConverter
from ifttt.parser.BooleanTokenConverter import BooleanTokenConverter
from ifttt.parser.CurrentTimeTokenConverter import CurrentTimeTokenConverter
from ifttt.parser.IntTokenConverter import IntTokenConverter
from ifttt.parser.SensorTokenConverter import SensorTokenConverter
from ifttt.parser.Tokenizer import Tokenizer
from listener.ChangeActuatorListener import ChangeActuatorListener
from listener.FingerprintDoorUnlockListener import FingerprintDoorUnlockListener
from listener.IntruderAlertListener import IntruderAlertListener
from listener.SaveLocationListener import SaveLocationListener
from listener.SetPhoneIsHomeListener import SetPhoneIsHomeListener
from locking.HomeAlarmLock import HomeAlarmLock
from locking.TimedLock import TimedLock
from repository.ActuatorsRepository import ActuatorsRepository
from repository.IftttRulesRepository import IftttRulesRepository
from repository.LocationTrackerRepository import LocationTrackerRepository
from repository.RoomsRepository import RoomsRepository
from repository.SensorsRepository import SensorsRepository
from repository.ConfigurationRepository import ConfigurationRepository
from sound.RemoteSpeaker import RemoteSpeaker
from sound.SoundApi import SoundApi
from tools.Authentication import Authentication
from tools.EmailNotifier import EmailNotifier
from tools.HomeDefence import HomeDefence
from tools.LoggingConfig import LoggingConfig
from tools.VoiceCommands import VoiceCommands
from web.factory.RuleFactory import RuleFactory
from web.factory.ConfigurationFactory import ConfigurationFactory
from web.formatter.ActuatorsFormatter import ActuatorsFormatter
from web.formatter.IftttFormatter import IftttFormatter
from web.formatter.RoomsFormatter import RoomsFormatter
from web.formatter.SensorsFormatter import SensorsFormatter
from web.formatter.ConfigurationFormatter import ConfigurationFormatter
from web.security.JwtTokenFactory import JwtTokenFactory
from model.Actuator import Actuator
from model.configuration.BluetoothCommunicationCfg import BluetoothCommunicationCfg
from model.configuration.EmailCfg import EmailCfg
from model.configuration.HomeDefenceCfg import HomeDefenceCfg
from model.configuration.SerialCommunicationCfg import SerialCommunicationCfg
from model.configuration.ZwaveCommunicationCfg import ZwaveCommunicationCfg


def singleton(function: Callable):
    caching = {}
    def wrapper(*args, **kwargs):
        if function.__name__ in caching:
            return caching[function.__name__]
        caching[function.__name__] = function(*args, **kwargs)

        return caching[function.__name__]

    return wrapper


class Container:
    @singleton
    def root_logger(self) -> RootLogger:
        logging_config = LoggingConfig(general.logging['log_file'], general.logging['log_entries'])
        sys.excepthook = logging_config.set_error_hadler

        return logging_config.get_logger(logging.INFO)

    @singleton
    def wemo_switch(self) -> WemoSwitch:
        return WemoSwitch(self.root_logger())

    def serial(self) -> Serial:
        return Serial(self.configuration_repository().get_config(SerialCommunicationCfg.get_classname()),
                      self.root_logger())

    def bluetooth_serial(self) -> SerialBluetooth:
        return SerialBluetooth(self.configuration_repository().get_config(BluetoothCommunicationCfg.get_classname()),
                      self.root_logger())

    @singleton
    def sound_api(self) -> SoundApi:
        return RemoteSpeaker(general.remote_speaker['host'], general.remote_speaker['user'],
                              general.remote_speaker['password'])

    @singleton
    def location_tracker_repository(self) -> LocationTrackerRepository:
        return LocationTrackerRepository(general.redis_config)

    @singleton
    def actuators_repository(self) -> ActuatorsRepository:
        return ActuatorsRepository(general.redis_config)

    @singleton
    def sensors_repository(self) -> SensorsRepository:
        return SensorsRepository(general.redis_config)

    @singleton
    def configuration_repository(self) -> ConfigurationRepository:
        return ConfigurationRepository(general.redis_config)

    @singleton
    def ifttt_rules_repository(self) -> IftttRulesRepository:
        return IftttRulesRepository(general.redis_config)

    @singleton
    def rooms_repository(self) -> RoomsRepository:
        return RoomsRepository(self.sensors_repository(), self.actuators_repository())

    @singleton
    def rooms_formatter(self) -> RoomsFormatter:
        return RoomsFormatter(self.rooms_repository())

    @singleton
    def sensors_formatter(self) -> SensorsFormatter:
        return SensorsFormatter(self.sensors_repository())

    @singleton
    def ifttt_formatter(self) -> IftttFormatter:
        return IftttFormatter(self.ifttt_rules_repository())

    @singleton
    def actuators_formatter(self) -> ActuatorsFormatter:
        return ActuatorsFormatter(self.actuators_repository())

    @singleton
    def configuration_formatter(self) -> ConfigurationFormatter:
        return ConfigurationFormatter(self.configuration_repository())

    @singleton
    def rule_factory(self) -> RuleFactory:
        return RuleFactory()

    @singleton
    def configuration_factory(self) -> ConfigurationFactory:
        return ConfigurationFactory()

    @singleton
    def incomming_zwave_communication_thread(self) -> IncommingZwaveCommunicationThread:
        return IncommingZwaveCommunicationThread(self.sensor_update_event(), self.sensors_repository(),
                                                 self.actuators_repository(), self.zwave_device(), self.root_logger())

    @singleton
    def sensors_polling_thread(self) -> SensorsPollingThread:
        return SensorsPollingThread(60, self.sensors_repository(), self.zwave_device(), self.sensor_update_event(),
                                    self.root_logger())

    @singleton
    def jwt_token_factory(self) -> JwtTokenFactory:
        return JwtTokenFactory(general.web_server['api_token_secret'])

    @singleton
    def email_notificator(self) -> EmailNotifier:
        return EmailNotifier(self.configuration_repository().get_config(EmailCfg.get_classname()),
                             self.configuration_repository().get_config(HomeDefenceCfg.get_classname()),
                             self.root_logger())

    @singleton
    def aes_encriptor(self) -> AesEncriptor:
        return AesEncriptor(general.communication['aes_key'])

    @singleton
    def zwave_device(self) -> ZWaveDevice:
        return ZWaveDevice(self.configuration_repository().get_config(ZwaveCommunicationCfg.get_classname()),
                           self.root_logger())

    @singleton
    def device_lifetime_manager(self) -> DeviceLifetimeManager:
        return DeviceLifetimeManager()

    @singleton
    def actuator_strategies(self) -> ActuatorStrategies:
        actuator_strategies = ActuatorStrategies()
        actuator_strategies.add_strategy(SerialSendStrategy(self.device_lifetime_manager(), self.aes_encriptor()))
        actuator_strategies.add_strategy(WemoSwitchStrategy(self.wemo_switch()))
        actuator_strategies.add_strategy(GroupStrategy(self.async_actuator_commands(), self.root_logger()))
        actuator_strategies.add_strategy(ZWaveStrategy(self.zwave_device()))

        return actuator_strategies

    @singleton
    def actuator_commands(self) -> ActuatorCommands:
        return ActuatorCommands(self.actuator_strategies(), self.actuators_repository(),
                                [Actuator.DeviceType.ACTION.value])

    @singleton
    def async_actuator_commands(self) -> AsyncActuatorCommands:
        return AsyncActuatorCommands(general.redis_config)

    @singleton
    def text_sensor_data_parser(self) -> TextSensorDataParser:
        return TextSensorDataParser(self.sensors_repository())

    @singleton
    def home_defence(self) -> HomeDefence:
        return HomeDefence(self.actuator_commands(), self.sound_api(), self.actuators_repository(),
                           self.configuration_repository().get_config(HomeDefenceCfg.get_classname()),
                           self.root_logger())

    @singleton
    def authentication(self) -> Authentication:
        return Authentication(general.credentials)

    @singleton
    def actuator_token_converter(self) -> ActuatorTokenConverter:
        return ActuatorTokenConverter(self.actuators_repository())

    @singleton
    def sensors_token_converter(self) -> SensorTokenConverter:
        return SensorTokenConverter(self.sensors_repository())

    @singleton
    def tokenizer(self) -> Tokenizer:
        tokenizer = Tokenizer(self.root_logger())
        tokenizer.add_token_converter(self.actuator_token_converter())
        tokenizer.add_token_converter(self.sensors_token_converter())
        tokenizer.add_token_converter(CurrentTimeTokenConverter())
        tokenizer.add_token_converter(ActuatorStateTokenConverter())
        tokenizer.add_token_converter(BooleanTokenConverter())
        tokenizer.add_token_converter(IntTokenConverter())

        return tokenizer

    @singleton
    def change_actuator_listener(self) -> ChangeActuatorListener:
        return ChangeActuatorListener(self.actuator_commands())

    @singleton
    def fingerprint_door_unlock_listener(self) -> FingerprintDoorUnlockListener:
        return FingerprintDoorUnlockListener(self.actuator_commands(), self.authentication())

    @singleton
    def intruder_alert_listener(self) -> IntruderAlertListener:
        return IntruderAlertListener(self.actuators_repository(), self.email_notificator(), self.home_alarm_lock())

    @singleton
    def save_location_listener(self) -> SaveLocationListener:
        return SaveLocationListener(self.location_tracker_repository())

    @singleton
    def set_phone_is_home_listener(self) -> SetPhoneIsHomeListener:
        return SetPhoneIsHomeListener(general.home_coordonates, self.sensors_repository(),
                                      self.location_tracker_repository())

    @singleton
    def change_actuator_request_event(self) -> ChangeActuatorRequestEvent:
        return ChangeActuatorRequestEvent()

    @singleton
    def sensor_update_event(self) -> SensorUpdateEvent:
        return SensorUpdateEvent()

    @singleton
    def text_communication_enhancer(self) -> TextCommunicationEnhancer:
        return TextCommunicationEnhancer(self.tokenizer())

    @singleton
    def command_executor(self) -> CommandExecutor:
        return CommandExecutor(self.change_actuator_request_event(), self.text_communication_enhancer(),
                               self.sound_api(), self.root_logger())

    @singleton
    def expression_validator(self) -> ExpressionValidator:
        return ExpressionValidator(self.tokenizer())

    @singleton
    def voice_commands(self) -> VoiceCommands:
        return VoiceCommands(self.async_actuator_commands(), self.root_logger()).configure()

    @singleton
    def timed_lock(self) -> TimedLock:
        return TimedLock(general.redis_config)

    @singleton
    def home_alarm_lock(self) -> HomeAlarmLock:
        alarm_lock_seconds = self.configuration_repository().\
            get_config(HomeDefenceCfg.get_classname()).alarm_lock_seconds

        return HomeAlarmLock(self.timed_lock(), alarm_lock_seconds)