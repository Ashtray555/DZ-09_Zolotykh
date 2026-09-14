# DZ-09: pytest test framework for ESP32-S3 firmware validation

This project contains a compact but structured pytest-based framework for automated validation of an embedded ESP32-S3 device.

## Architecture

- `DeviceDriver` is the single communication layer and owns all device-specific logic.
- `FakeDevice` models the firmware state in memory to keep validation deterministic and CI-friendly.
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

## Notes

- boot wait uses the firmware pattern `App started` instead of `sleep()`
- no device is instantiated directly inside tests
- all protocol/firmware logic remains inside the driver for isolation and maintainability
- the suite is intentionally deterministic so it can be run in CI without hardware-specific assumptions
