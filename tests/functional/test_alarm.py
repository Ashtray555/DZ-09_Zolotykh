import pytest


@pytest.mark.parametrize(
    ("sensor_value", "threshold", "expected_state"),
    [
        (20, 80, "ARMED"),
        (90, 80, "TRIGGERED"),
        (60, 40, "TRIGGERED"),
    ],
)
def test_alarm_arms_and_triggers(device_driver, sensor_value, threshold, expected_state):
    device_driver.backend.sensor_value = sensor_value
    device_driver.backend.alarm_threshold = threshold

    status = device_driver.alarm_arm()

    assert status["state"] == expected_state
    assert status["threshold"] == threshold


@pytest.mark.parametrize(
    ("sensor_value", "threshold"),
    [
        (90, 80),
        (50, 30),
    ],
)
def test_alarm_can_clear_triggered_state(device_driver, sensor_value, threshold):
    device_driver.backend.sensor_value = sensor_value
    device_driver.backend.alarm_threshold = threshold
    device_driver.alarm_arm()

    status = device_driver.clear_alarm()

    assert status["state"] == "CLEARED"
    assert status["led_state"] == "OFF"


@pytest.mark.parametrize(
    "state",
    [
        "DISARMED",
        "ARMED",
    ],
)
def test_alarm_disarm_resets_state(device_driver, state):
    device_driver.backend.alarm_state = state

    status = device_driver.alarm_disarm()

    assert status["state"] == "DISARMED"
    assert status["led_state"] == "OFF"
