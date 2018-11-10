from typeguard import typechecked


class LocationEvent:
    NAME = 'location'

    @typechecked()
    def __init__(self, device_name: str, latitude: float, longitude: float):
        self.__device_name = device_name
        self.__latitude = latitude
        self.__longitude = longitude

    @typechecked()
    def get_device_name(self) -> str:
        return self.__device_name

    @typechecked()
    def get_latitude(self) -> float:
        return self.__latitude

    @typechecked()
    def get_longitude(self) -> float:
        return self.__longitude