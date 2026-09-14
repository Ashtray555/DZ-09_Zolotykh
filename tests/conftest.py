import pytest

from dz09 import DeviceDriver


@pytest.fixture
def device_driver():
    """Create a fresh device session per test, following the required fixture-based pattern."""
    driver = DeviceDriver(vid=0x303A, use_fake_backend=True)
    driver.wait_for_pattern("App started")
    driver.reset()
    return driver
