def test_device_reports_ready_after_boot(device_driver):
    status = device_driver.reboot()
    device_driver.restore_session()

    assert status["ready"] is True
    assert device_driver.status()["ready"] is True


def test_device_status_reports_led_state(device_driver):
    status = device_driver.status()

    assert status["ready"] is True
    assert status["led"] in {"ON", "OFF"}


def test_default_alarm_state_is_disarmed(device_driver):
    alarm_status = device_driver.alarm_status()

    assert alarm_status["state"] == "DISARMED"
    assert alarm_status["threshold"] == 80
    assert alarm_status["led_state"] in {"OFF", "ON"}
