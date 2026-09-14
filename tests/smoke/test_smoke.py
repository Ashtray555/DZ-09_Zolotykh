def test_device_reports_ready_after_boot(device_driver):
    status = device_driver.reboot()

    assert device_driver.wait_for_pattern("App started") is True
    assert status["ready"] is True
    assert "App started" in status["boot_log"]


def test_distance_sensor_returns_valid_range(device_driver):
    distance = device_driver.read_distance()

    assert 1 <= distance <= 400


def test_default_alarm_state_is_disarmed(device_driver):
    alarm_status = device_driver.alarm_status()

    assert alarm_status["state"] == "DISARMED"
    assert alarm_status["threshold"] == 80
    assert alarm_status["led_state"] in {"OFF", "ON"}
