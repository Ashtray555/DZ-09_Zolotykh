# Real Hardware Pytest Evidence

- Date: 2026-09-23
- Device: ESP32-S3 connected through a CH343 USB-UART adapter
- UART: 115200 8N1
- Port selection: automatic discovery by USB VID `0x1A86`
- Command: `python -m pytest -v`

## Result

```text
collected 12 items

7 alarm tests: passed
1 persistence test: xfailed
1 distance stability test: skipped
3 smoke tests: passed

10 passed, 1 skipped, 1 xfailed in 38.10s
```

## Known Firmware Result

`test_config_values_are_saved_and_loaded` is a strict `xfail`: firmware reports a successful `config save`, but after `reboot` and `config load`, the saved configuration is not restored.

## Distance Test Status

`test_distance_readings_are_stable` is skipped until an HC-SR04 is connected with a safe 5V-to-3.3V level shifter on `ECHO`.
