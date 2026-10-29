"""Tests for the Rotarex Dimes Wave BLE parser."""

from __future__ import annotations

import pytest
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import DeviceClass

from rotarex_dimes_ble import (
    DeviceKey,
    Region,
    RotarexDimesBluetoothDeviceData,
    SensorDescription,
    SensorDeviceInfo,
    SensorUpdate,
    SensorValue,
    TankType,
    Units,
    convert_level,
)

SERVICE_UUID = "2b67836a-183d-45da-a1bf-381b05e1bde8"
ADDRESS = "AA:BB:CC:DD:EE:FF"


def make_service_info(
    payload: bytes,
    service_uuids: list[str] | None = None,
    manufacturer_id: int = 0xFFFF,
) -> BluetoothServiceInfo:
    return BluetoothServiceInfo(
        name="SRG-1-WAVE",
        address=ADDRESS,
        rssi=-69,
        manufacturer_data={manufacturer_id: payload},
        service_data={},
        service_uuids=[SERVICE_UUID] if service_uuids is None else service_uuids,
        source="local",
    )


# Payloads captured from a real Dimes Wave sensor
CAPTURED_FULL_BATTERY = bytes.fromhex("00591414")  # battery 89 %, raw level 20 %
CAPTURED_LOW_BATTERY = bytes.fromhex("000a2929")  # battery 10 %, raw level 41 %


def test_parse_captured_advertisement() -> None:
    parser = RotarexDimesBluetoothDeviceData(Region.OTHER, TankType.CYLINDER)
    assert parser.supported(make_service_info(CAPTURED_FULL_BATTERY))
    assert parser.update(make_service_info(CAPTURED_FULL_BATTERY)) == SensorUpdate(
        title="SRG-1-WAVE EEFF",
        devices={
            None: SensorDeviceInfo(
                name="SRG-1-WAVE EEFF",
                model="Dimes Wave",
                manufacturer="Rotarex",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="level", device_id=None): SensorDescription(
                device_key=DeviceKey(key="level", device_id=None),
                device_class=None,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=89,
            ),
            DeviceKey(key="level", device_id=None): SensorValue(
                device_key=DeviceKey(key="level", device_id=None),
                name="Level",
                native_value=20,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-69,
            ),
        },
    )


@pytest.mark.parametrize(
    ("region", "tank_type", "expected_level"),
    [
        (Region.EUROPE, TankType.CAMPING_CYLINDER, 43),
        (Region.EUROPE, TankType.CYLINDER, 43),
        (Region.EUROPE, TankType.TANK, 43),
        (Region.EUROPE, TankType.CAMPING_TANK, 42),
        (Region.EUROPE, TankType.CAMPING_SMART, 41),
        (Region.OTHER, TankType.CAMPING_CYLINDER, 41),
        (Region.OTHER, TankType.CAMPING_TANK, 42),
        (Region.OTHER, TankType.CAMPING_SMART, 41),
    ],
)
def test_level_conversion_per_setting(
    region: Region, tank_type: TankType, expected_level: int
) -> None:
    parser = RotarexDimesBluetoothDeviceData(region, tank_type)
    update = parser.update(make_service_info(CAPTURED_LOW_BATTERY))
    level = update.entity_values[DeviceKey(key="level", device_id=None)]
    battery = update.entity_values[DeviceKey(key="battery", device_id=None)]
    assert level.native_value == expected_level
    assert battery.native_value == 10


@pytest.mark.parametrize(
    ("raw_level", "region", "tank_type", "expected"),
    [
        (0, Region.EUROPE, TankType.CAMPING_CYLINDER, 14),
        (100, Region.EUROPE, TankType.CAMPING_CYLINDER, 84),
        (100, Region.EUROPE, TankType.CAMPING_TANK, 100),
        (99, Region.OTHER, TankType.CAMPING_TANK, 100),
        (0, Region.OTHER, TankType.CYLINDER, 0),
    ],
)
def test_convert_level_edges(
    raw_level: int, region: Region, tank_type: TankType, expected: int
) -> None:
    assert convert_level(raw_level, region, tank_type) == expected


@pytest.mark.parametrize(
    "service_info",
    [
        pytest.param(make_service_info(bytes(4)), id="reset_zeros"),
        pytest.param(make_service_info(bytes.fromhex("005914")), id="short"),
        pytest.param(make_service_info(bytes.fromhex("00651414")), id="battery_101"),
        pytest.param(make_service_info(bytes.fromhex("00596514")), id="level_101"),
        pytest.param(
            make_service_info(CAPTURED_FULL_BATTERY, service_uuids=[]),
            id="no_service_uuid",
        ),
        pytest.param(
            make_service_info(CAPTURED_FULL_BATTERY, manufacturer_id=0x0059),
            id="other_manufacturer",
        ),
    ],
)
def test_ignored_advertisements(service_info: BluetoothServiceInfo) -> None:
    parser = RotarexDimesBluetoothDeviceData()
    assert not parser.supported(service_info)
