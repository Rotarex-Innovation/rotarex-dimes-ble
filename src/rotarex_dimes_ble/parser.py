"""Parser for Rotarex Dimes Wave BLE advertisements."""

from __future__ import annotations

import logging

from bluetooth_data_tools import short_address
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import SensorLibrary, Units

from .models import Region, TankType

_LOGGER = logging.getLogger(__name__)

SERVICE_UUID = "2b67836a-183d-45da-a1bf-381b05e1bde8"
# The sensors use the Bluetooth SIG reserved company identifier
MANUFACTURER_ID = 0xFFFF
PAYLOAD_LENGTH = 4


def convert_level(raw_level: int, region: Region, tank_type: TankType) -> int:
    """Convert the raw level to the level shown in the ROTAREX DIMES app."""
    if tank_type is TankType.CAMPING_TANK:
        return raw_level if raw_level == 100 else raw_level + 1
    if region is Region.EUROPE and tank_type is not TankType.CAMPING_SMART:
        return round((raw_level * 0.007 + 0.1407) * 100)
    return raw_level


class RotarexDimesBluetoothDeviceData(BluetoothData):
    """Data for Rotarex Dimes Wave BLE sensors."""

    def __init__(
        self,
        region: Region = Region.EUROPE,
        tank_type: TankType = TankType.CAMPING_CYLINDER,
    ) -> None:
        super().__init__()
        self._region = region
        self._tank_type = tank_type

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        if (
            SERVICE_UUID not in service_info.service_uuids
            or MANUFACTURER_ID not in service_info.manufacturer_data
        ):
            return
        data = service_info.manufacturer_data[MANUFACTURER_ID]
        if len(data) != PAYLOAD_LENGTH:
            _LOGGER.debug("Unexpected Rotarex payload length: %s", data.hex())
            return
        # The sensor advertises zeros right after a battery change or power on
        if not any(data):
            return
        battery, raw_level = data[1], data[2]
        if battery > 100 or raw_level > 100:
            _LOGGER.debug("Out of range Rotarex payload: %s", data.hex())
            return

        name = (
            f"{service_info.name or 'Dimes Wave'} {short_address(service_info.address)}"
        )
        self.set_title(name)
        self.set_device_manufacturer("Rotarex")
        self.set_device_type("Dimes Wave")
        self.set_device_name(name)
        self.update_predefined_sensor(SensorLibrary.BATTERY__PERCENTAGE, battery)
        self.update_sensor(
            key="level",
            native_unit_of_measurement=Units.PERCENTAGE,
            native_value=convert_level(raw_level, self._region, self._tank_type),
            name="Level",
        )
