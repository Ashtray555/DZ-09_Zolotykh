import os
import time

import pytest

from dz09 import DeviceDriver


def pytest_addoption(parser):
    parser.addoption(
        "--transport",
        choices=("serial", "mock"),
        default="serial",
        help="Device transport; serial is the default, mock is for CI only.",
    )
    parser.addoption(
        "--device-vid",
        default="0x1A86",
        help="USB-UART adapter vendor ID used for automatic port discovery.",
    )


@pytest.fixture(scope="session")
def device_driver(request):
    """Create one authenticated device session through the selected transport."""
    transport = request.config.getoption("--transport")
    vid = int(request.config.getoption("--device-vid"), 0)
    driver = DeviceDriver(vid=vid, transport=transport)
    login = f"qa{int(time.time()) % 1000000000}"
    password = "QaPass123"
    try:
        if transport == "serial":
            driver.register(login, password)
            driver.login(login, password)
        yield driver
    finally:
        driver.close()
