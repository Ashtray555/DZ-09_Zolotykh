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
    try:
        device_driver.sensor_start()
        device_driver.set_sensor_value(sensor_value)
        device_driver.set_alarm_threshold(threshold)

        status = device_driver.alarm_arm()

        assert status["state"] == expected_state
        assert status["threshold"] == threshold
    finally:
        device_driver.alarm_disarm()
        device_driver.sensor_stop()
        device_driver.set_alarm_threshold(80)


@pytest.mark.parametrize(
    ("sensor_value", "threshold"),
    [
        (90, 80),
        (50, 30),
    ],
)
def test_alarm_can_clear_triggered_state(device_driver, sensor_value, threshold):
    try:
        device_driver.sensor_start()
        device_driver.set_sensor_value(sensor_value)
        device_driver.set_alarm_threshold(threshold)
        device_driver.alarm_arm()
        triggered = device_driver.wait_for_alarm_state("TRIGGERED")

        status = device_driver.clear_alarm()

        assert triggered["state"] == "TRIGGERED"
        assert status["state"] == "CLEARED"
        assert status["led_state"] == "OFF"
    finally:
        device_driver.alarm_disarm()
        device_driver.sensor_stop()
        device_driver.set_alarm_threshold(80)


@pytest.mark.parametrize(
    "sensor_value",
    [
        20,
        100,
    ],
)
def test_alarm_disarm_resets_state(device_driver, sensor_value):
    try:
        device_driver.sensor_start()
        device_driver.set_sensor_value(sensor_value)
        device_driver.alarm_arm()

        status = device_driver.alarm_disarm()

        assert status["state"] == "DISARMED"
        assert status["led_state"] == "OFF"
    finally:
        device_driver.sensor_stop()
        device_driver.set_alarm_threshold(80)
