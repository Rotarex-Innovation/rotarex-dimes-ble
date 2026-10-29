# Rotarex Dimes Wave BLE

Parser for the Bluetooth Low Energy advertisements of Rotarex Dimes Wave gas level sensors, the sensors used with the ROTAREX DIMES app. It is the library behind the Home Assistant `rotarex_ble` integration.

The sensors broadcast their battery level and raw gas level in their advertisements, so they can be read passively, without connecting to them.

## Installation

```bash
pip install rotarex-dimes-ble
```

## Usage

The parser builds on [bluetooth-sensor-state-data](https://github.com/Bluetooth-Devices/bluetooth-sensor-state-data). Pass it the advertisement as a `BluetoothServiceInfo`:

```python
from home_assistant_bluetooth import BluetoothServiceInfo

from rotarex_dimes_ble import Region, RotarexDimesBluetoothDeviceData, TankType

parser = RotarexDimesBluetoothDeviceData(Region.EUROPE, TankType.CAMPING_CYLINDER)
update = parser.update(service_info)  # a SensorUpdate with level, battery and signal strength
```

### Level conversion

The sensor reports a raw level. Like the ROTAREX DIMES app, the parser converts it depending on the unit region and the tank type selected in the app:

| Region | Tank type | Level |
| --- | --- | --- |
| Any | Camping tank | raw + 1 (100 stays 100) |
| Europe | Camping cylinder, cylinder, tank | round((raw × 0.007 + 0.1407) × 100) |
| Europe | Camping smart | raw |
| Other | Any other type | raw |

## Advertisement format

- Service UUID: `2b67836a-183d-45da-a1bf-381b05e1bde8`
- Manufacturer data, company identifier `0xFFFF`, 4 bytes:
  - byte 0: not used
  - byte 1: battery level in %
  - byte 2: raw gas level in %
  - byte 3: not used
- The data is in the main advertisement packet, not the scan response, so passive scanning is enough.
- The sensor advertises continuously, but refreshes the measured values every 20 minutes.
- A payload of only zeros is sent right after a battery change or power on and is ignored.

## Development

```bash
pip install -e ".[test]"
ruff check src tests
mypy src
pytest
```

## License

MIT, see [LICENSE](LICENSE).
