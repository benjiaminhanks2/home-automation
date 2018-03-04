from typing import Callable
from typing import Any
from logging import RootLogger

from typeguard import typechecked
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
from pydispatch import dispatcher

from communication.DeviceLifetimeCycles import DeviceLifetimeCycles
from model.configuration.ZwaveCommunicationCfg import ZwaveCommunicationCfg


class ZWaveDevice(DeviceLifetimeCycles):
    @typechecked()
    def __init__(self, zwave_config: ZwaveCommunicationCfg, root_logger: RootLogger) -> None:
        self.__zwave_config = zwave_config
        self.__root_logger = root_logger
        self.__network = None
        self.__state_change_callback = None

    def connect(self) -> None:
        options = ZWaveOption(self.__zwave_config.port,
                              config_path=self.__zwave_config.openzwave_config_path,
                              user_path=".", cmd_line="")
        options.set_console_output(False)
        options.set_save_log_level("None")
        options.set_logging(False)
        options.lock()
        self.__network = ZWaveNetwork(options, autostart=False)
        dispatcher.connect(self.__network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
        dispatcher.connect(self.__network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)
        dispatcher.connect(self.__value_update, ZWaveNetwork.SIGNAL_VALUE)
        self.__network.start()

    def disconnect(self) -> None:
        self.__root_logger.info('Disconnectiong Zwave device')
        self.__network.stop()

    @typechecked()
    def attach_state_change_callback(self, callback: Callable[[str, Any], None]):
        self.__state_change_callback = callback

    @typechecked()
    def change_switch(self, switch_id: str, state: bool) -> bool:
        node, val = self.__get_node(switch_id, 'switch')
        try:
            node.set_switch(val, state)
        except Exception as e:
            return False
        return True

    @typechecked()
    def change_dimmer(self, switch_id: str, state: int) -> bool:
        try:
            node, val = self.__get_node(switch_id, 'dimmer')
            node.set_dimmer(val, state)
        except Exception as e:
            return False
        return True

    @typechecked()
    def get_sensor_value(self, sensor_id: str):
        try:
            node, val = self.__get_node(sensor_id, 'sensor')
            return node.get_sensor_value(val)
        except Exception as e:
            return None

    @typechecked()
    def __get_node(self, actuator_name: str, type: str):
        for node in self.__network.nodes:
            for val in self.__get_device_by_type(self.__network.nodes[node], type):
                self.__root_logger.info('Zwave node: {0}'.format(
                    self.__network.nodes[node].values[val].id_on_network)
                )
                if self.__network.nodes[node].values[val].id_on_network != actuator_name:
                    continue
                self.__root_logger.info('Changing zwave switch: {0}'.format(actuator_name))
                return self.__network.nodes[node], val

        raise Exception('Zwave node with id {0} not found'.format(actuator_name))

    @typechecked()
    def __get_device_by_type(self, node, type: str):
        if type == 'switch':
            return node.get_switches()
        elif type == 'sensor':
            return node.get_sensors()
        elif type == 'dimmer':
            return node.get_dimmers()

    def __network_failed(self, network):
        self.__root_logger.info('Zwave network failed loading')

    def __network_ready(self, network):
        self.__root_logger.info('Zwave network ready, contoler name: {0}'.format(network.controller))

    def __value_update(self, network, node, value):
        self.__root_logger.info('Updating zwave id {0} with new value: {1}'.format(value.id_on_network, value.data))
        if None is self.__state_change_callback:
            return
        self.__state_change_callback(value.id_on_network, value.data)