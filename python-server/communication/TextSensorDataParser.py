import re
from typing import List

from typeguard import typechecked

from communication.SensorsParseException import SensorsParseException
from repository.SensorsRepository import SensorsRepository
from model.Sensor import Sensor
from model.SensorProperties import SensorProperties

class TextSensorDataParser:
    SENSOR_REGEX = '([A-Z]{1,2})(\d{1,2})?\:([\d\-\.]{1,4})'
    SENSOR_SEPARATOR = '|'

    @typechecked()
    def __init__(self, sensors_repo: SensorsRepository):
        self.__sensors_repo = sensors_repo

    @typechecked()
    def is_buffer_parsable(self, buffer: str) -> bool:
        return buffer.endswith(self.SENSOR_SEPARATOR)

    @typechecked()
    def parse(self, text_buffer: str) -> List[Sensor]:
        text_buffer = text_buffer[:-1]
        sensors = []
        for sensor in text_buffer.split('|'):
            sensor_components = re.findall(self.SENSOR_REGEX, sensor)
            if not sensor_components:
                raise SensorsParseException('Cannot parse string:{0}'.format(sensor))
            sensors.append(self.__get_sensor(sensor_components[0]))

        return sensors

    def __get_sensor(self, sensor_components) -> Sensor:
        code = sensor_components[0]
        if sensor_components[1] == '':
            location = False
        else:
            location = sensor_components[1]
        value = sensor_components[2]
        for sensor in self.__sensors_repo.get_sensors():
            communication_code = sensor.properties.get(SensorProperties.COMMUNICATOR_CODE)
            if None is communication_code:
                continue
            if communication_code[0] == code and communication_code[1] == location:
                try:
                    sensor.value = int(value)
                except ValueError as e:
                    raise SensorsParseException(
                        'Badly formatted sensor value: {0}, error: {1})'.format(value, e.message))
                return sensor

        raise SensorsParseException('Sensor with code: {0} and location {1} not found!'.format(code, location))