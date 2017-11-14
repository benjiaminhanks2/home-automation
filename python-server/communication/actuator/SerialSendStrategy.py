import time

from typeguard import typechecked

from .BaseStrategy import BaseStrategy
from communication.SerialCommunicatorRegistry import SerialCommunicatorRegistry
from repository.ActuatorsRepository import ActuatorsRepository
from model.Actuator import Actuator
from model.ActuatorType import ActuatorType
from model.ActuatorProperties import ActuatorProperties
from communication.encriptors.AesEncriptor import AesEncriptor


class SerialSendStrategy(BaseStrategy):
    @typechecked()
    def __init__(self, communicator_registry: SerialCommunicatorRegistry, actuators_repo: ActuatorsRepository,
                 encriptor: AesEncriptor):
        self.__communicator_registry = communicator_registry
        self.__actuators_repo = actuators_repo
        self.__encriptor = encriptor

    @typechecked()
    def supports(self, actuator_name: str) -> bool:
        actuator = self.__actuators_repo.get_actuators()[actuator_name]

        return actuator.device_type == Actuator.DeviceType.SERIAL.value \
               and actuator.type in [ActuatorType.SWITCH.value, ActuatorType.PUSHBUTTON.value]

    @typechecked()
    def set_state(self, actuator_name: str, state):
        actuator = self.__actuators_repo.get_actuators()[actuator_name]
        command = self.__encrypt(self.__calculate_actuator_command(actuator, state), actuator)
        send_to_device = actuator.properties.get(ActuatorProperties.SEND_TO_DEVICE)
        communicator = actuator.properties.get(ActuatorProperties.COMMUNICATOR)
        self.__communicator_registry. \
            get_communicator(communicator). \
            send(send_to_device, command)
        time.sleep(0.5)

        return True

    # todo remove this hack: actuator_command[{True: 'true', False: 'false'}[state]]
    def __calculate_actuator_command(self, actuator: Actuator, state: bool):
        actuator_type = actuator.type
        actuator_command = actuator.properties.get(ActuatorProperties.COMMAND)
        if actuator_type == ActuatorType.SWITCH.value:
            return actuator_command[{True: 'true', False: 'false'}[state]]
        elif actuator_type == ActuatorType.PUSHBUTTON.value:
            return actuator_command['true']
        else:
            raise Exception('Unimplemented actuator type: %s'.format(actuator_type))

    def __encrypt(self, text: str, actuator: Actuator):
        encription = actuator.properties.get(ActuatorProperties.ENCRIPTION)
        if None == encription:
            return text

        return self.__encriptor.encrypt(text)


