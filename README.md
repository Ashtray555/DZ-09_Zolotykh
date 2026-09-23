# DZ-09: pytest test framework for ESP32-S3 firmware validation

This project contains a compact but structured pytest-based framework for automated validation of an embedded ESP32-S3 device.

## Architecture

- `DeviceDriver` is the single communication layer and owns all device-specific logic.
- The default transport is real UART at `115200 8N1`, discovered by the USB-UART adapter VID (`0x1A86` for the verified CH343 adapter).
- `FakeDevice` is an explicit `--transport=mock` fallback for CI; it is never selected by the default test command.
- tests access the device only through the `device_driver` fixture, which keeps setup consistent with the assignment rules.
- port discovery is performed by VID-based auto-detection; no COM name is hardcoded.

## Test strategy

The framework separates validation into two layers:

- `smoke` checks validate baseline readiness and a minimal device health status.
- `functional` checks validate the alarm logic, configuration persistence, and sensor stability under repeated reads.

This distinction keeps the suite fast, predictable, and aligned with the embedded QA workflow.

## Requirements traceability

| Homework item | Coverage |
|---|---|
| Structure + conftest + fixtures | [tests/conftest.py](tests/conftest.py) |
| Smoke tests | [tests/smoke/test_smoke.py](tests/smoke/test_smoke.py) |
| Parameterized alarm tests | [tests/functional/test_alarm.py](tests/functional/test_alarm.py) |
| Persistence/config test | [tests/functional/test_config.py](tests/functional/test_config.py) |
| Distance stability test | [tests/functional/test_distance_stability.py](tests/functional/test_distance_stability.py) |
| Device protocol encapsulation | [src/dz09/device_driver.py](src/dz09/device_driver.py) |
| VID-based port search | [src/dz09/device_driver.py](src/dz09/device_driver.py) |
| Boot wait without sleep | [src/dz09/device_driver.py](src/dz09/device_driver.py) |

## Run

```bash
cd dz09
python -m pip install -r requirements.txt
python -m pytest -v
```

Before the real-device run, press `RST` once so the firmware starts with an empty RAM-only user profile. The fixture registers a disposable user, logs in through UART, and uses the real device for all non-skipped tests.

The mock fallback is available only when explicitly requested:

```bash
python -m pytest --transport=mock -v
```

Pass a different adapter VID only when using another USB-UART bridge:

```powershell
python -m pytest --device-vid 0x1A86 -v
```

## Verified Hardware Results

- Default command `python -m pytest -v` completed on the connected ESP32-S3: `10 passed, 1 skipped, 1 xfailed`.
- UART registration, login, status, and manual sensor alarm trigger passed.
- The alarm triggers for manual value `100` at threshold `80`.
- `config save` reports success, but the setting is lost after `reboot`; this is tracked as a strict expected failure (`XFAIL`).
- The distance test remains skipped until an HC-SR04 is connected with `TRIG -> GPIO5`, `ECHO -> GPIO18` through a 5V-to-3.3V level shifter. Enable it only after safe wiring with `DZ09_DISTANCE_READY=1`.

## Notes

- reboot waits for the firmware's real UART boot marker `Device ready`; no `time.sleep()` is used for boot synchronization
- no device is instantiated directly inside tests
- all protocol/firmware logic remains inside the driver for isolation and maintainability
- the optional mock transport is intended only for CI without attached hardware
