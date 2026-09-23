import os

import pytest


@pytest.mark.skipif(
    os.getenv("DZ09_DISTANCE_READY") != "1",
    reason="Connect HC-SR04 with a level-shifted ECHO line, then set DZ09_DISTANCE_READY=1.",
)
def test_distance_readings_are_stable(device_driver):
    readings = device_driver.read_distance_series(10)

    assert len(readings) == 10
    assert max(readings) - min(readings) <= 2
    assert all(1 <= value <= 400 for value in readings)
