import pytest


@pytest.mark.xfail(
    strict=True,
    reason="Firmware reports config save success but loses fake NVS data after reboot.",
)
def test_config_values_are_saved_and_loaded(device_driver):
    if device_driver.transport == "mock":
        pytest.skip("Persistence regression is verified against the real firmware only.")

    device_driver.config_set("alarm_threshold", 42)
    assert device_driver.config_get("alarm_threshold") == 42

    device_driver.config_save()
    device_driver.reboot()
    device_driver.restore_session()
    device_driver.config_load()

    assert device_driver.config_get("alarm_threshold") == 42
