"""Embedded QA testing framework for the ESP32-S3 device."""

from .device_driver import DeviceDriver, FakeDevice

__all__ = ["DeviceDriver", "FakeDevice"]
