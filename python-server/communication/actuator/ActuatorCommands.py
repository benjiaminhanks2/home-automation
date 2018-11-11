from typing import List

from typeguard import typechecked

from communication.actuator.ActuatorStrategies import ActuatorStrategies
from communication.actuator.strategies.BaseStrategy import BaseStrategy
from repository.ActuatorsRepository import ActuatorsRepository
from model.Actuator import Actuator


class ActuatorCommands:
    @typechecked()
    def __init__(self, actuator_strategies: ActuatorStrategies, actuators_repo: ActuatorsRepository,
                 excluded_actuator_device_types: List[str], logger):
        self.__actuator_strategies = actuator_strategies
        self.__actuators_repo = actuators_repo
        self.__excluded_actuator_device_types = excluded_actuator_device_types
        self.__logger = logger

    @typechecked()
    def change_actuator(self, id: str, state):
        actuator = self.__actuators_repo.get_actuator(id)
        self.__actuators_repo.set_actuator_state(id, state)
        if actuator.device_type in self.__excluded_actuator_device_types:
            return True
        strategy = self.__get_strategy(actuator)
        success = strategy.set_state(actuator, state)
        if not success and actuator.type == Actuator.ActuatorType.SWITCH.value:
            self.__actuators_repo.set_actuator_state(id, not state)

        return success

    @typechecked()
    def __get_strategy(self, actuator: Actuator) -> BaseStrategy:
        strategies = self.__actuator_strategies.get_strategies()
        try:
            return [strategy for strategy in strategies if strategy.supports(actuator)][0]
        except IndexError:
            raise NotImplementedError('Actuator {0} does not have a strategy associated. Check "device_type"'
                                      .format(actuator))