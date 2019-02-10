import collections
import json
from typing import Dict
from typing import Optional

from typeguard import typechecked

from repository.AbstractRepository import AbstractRepository
from model.Actuator import Actuator
from model.ActuatorProperties import ActuatorProperties
from tools.RetryPattern import RetryPattern


class ActuatorsRepository(AbstractRepository):
    __REDIS_KEY = 'actuators'

    @typechecked()
    def __init__(self, redis_configuration: dict, retry_pattern: RetryPattern):
        AbstractRepository.__init__(self, redis_configuration)
        self.__retry_pattern = retry_pattern
        self.keys = {self.__REDIS_KEY: {}}

    @typechecked()
    def get_actuators(self) -> Dict[str, Actuator]:
        actuators_data = self.get(self.__REDIS_KEY)
        actuators = {}
        for id, data in actuators_data.items():
            actuator = Actuator(id, data['name'], data['value'], data['type'], data['room'], data['device_type'])
            actuator.properties = self.__get_actuator_properties(data['properties'])
            actuators[id] = actuator

        return collections.OrderedDict(sorted(actuators.items()))

    @typechecked()
    def get_actuator(self, id: str) -> Optional[Actuator]:
        return self.get_actuators().get(id)

    @typechecked()
    def set_actuator_state(self, id: str, value) -> None:
        def wrapper():
            return self.__set(self.__REDIS_KEY, id, value)
        return self.__retry_pattern.run(wrapper, 3)

    # this is a temporary method and will be replaced with a set actuator method
    @typechecked()
    def set_actuators(self, actuators: list):
        indexes_by_id = {actuator['id']: actuator for actuator in actuators}
        self.client.set(self.__REDIS_KEY, json.dumps(indexes_by_id))

    def __set(self, key, id, value):
        data = self.get(key)
        data[id]['value'] = value
        self.client.set(key, json.dumps(data))

    def __get_actuator_properties(self, properties: dict) -> ActuatorProperties:
        actuator_properties = ActuatorProperties()
        for name, value in properties.items():
            actuator_properties.set(name, value)

        return actuator_properties