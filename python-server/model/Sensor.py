from typing import Tuple
from enum import Enum


class Sensor:
    class SensorType(Enum):
        HUMIDITY = 'humidity'
        TEMPERATURE = 'temperature'
        AIR_PRESSURE = 'airPressure'
        LIGHT = 'light'
        VOLTAGE = 'voltage'
        RAIN = 'rain'
        PRESENCE = 'presence'
        AIR_POLLUTION = 'airPollution'
        FINGERPRINT = 'fingerprint'
        PHONE_IS_HOME = 'phoneIsHome'
        FLOOD = 'flood'
        POWER = 'power'

    def __init__(self, id: str, type: str, location: str, value) -> None:
        self.id = id
        self.type = type
        self.location = location
        self.value = value
        self._communication_code = None
        self._last_updated = None
        self._name = None

    @property
    def communication_code(self) -> Tuple:
        return self._communication_code

    @communication_code.setter
    def communication_code(self, value: Tuple):
        self._communication_code = value

    @property
    def last_updated(self):
        return self._last_updated

    @last_updated.setter
    def last_updated(self, value):
        self._last_updated = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __repr__(self) -> str:
        return "Sensor: type({0}), location({1}), value({2})," \
               " communication_code({3}), last_updated({4}), name({5})".format(self.type, self.location, self.value,
                                                                     self._communication_code, self._last_updated,
                                                                    self._name)