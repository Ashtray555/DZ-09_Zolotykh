def test_config_values_are_saved_and_loaded(device_driver):
    device_driver.config_set("sensor_interval", 5000)
    assert device_driver.config_get("sensor_interval") == 5000
    assert device_driver.backend.nvs["saved"] is False

    device_driver.config_save()
    assert device_driver.backend.nvs["saved"] is True

    device_driver.config_set("alarm_threshold", 200)
    device_driver.config_load()

    assert device_driver.config_get("sensor_interval") == 5000
    assert device_driver.config_get("alarm_threshold") == 80


def test_config_default_values_are_used_when_missing(device_driver):
    device_driver.backend.nvs = {"sensor_interval": 3000, "alarm_threshold": 80, "dist_threshold": 50, "saved": False}

    device_driver.config_load()

    assert device_driver.config_get("sensor_interval") == 3000
    assert device_driver.config_get("alarm_threshold") == 80
    assert device_driver.config_get("dist_threshold") == 50
