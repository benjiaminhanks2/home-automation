from logging import RootLogger

from typeguard import typechecked
from event.ChangeActuatorRequestEvent import ChangeActuatorRequestEvent
from sound.SoundApi import SoundApi
from ifttt.command.TextCommunicationEnhancer import TextCommunicationEnhancer
from model.RuleCommand import RuleCommand


class CommandExecutor:
    @typechecked()
    def __init__(self, change_actuator_request_event: ChangeActuatorRequestEvent,
                 text_communication_enhancer: TextCommunicationEnhancer,
                 sound_api : SoundApi, logging: RootLogger):
        self.__change_actuator_request_event = change_actuator_request_event
        self.__text_communication_enhancer = text_communication_enhancer
        self.__sound_api = sound_api
        self.__logging = logging

    @typechecked()
    def execute(self, command: RuleCommand) -> None:
        if None is not command.voice_text and command.voice_text is not '':
            enhanced_text = self.__text_communication_enhancer.enhance(command.voice_text)
            self.__sound_api.say(enhanced_text)
            self.__logging.info('Speaking text: {0}'.format(command.voice_text))
        if None is not command.actuator_id and '' is not command.actuator_id\
                and None is not command.actuator_state and '' is not command.actuator_state:
            self.__logging.info('Changing actuator: {0} to new value: {1}'
                                 .format(command.actuator_id, command.actuator_state))
            self.__change_actuator_request_event.send(command.actuator_id, command.actuator_state)