from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None


@dataclass
class FakeDevice:
    """In-memory device model that behaves like the ESP32-S3 firmware state."""

    app_started: bool = True
    boot_log: list[str] = field(default_factory=lambda: ["App started"])
    distance: int = 42
    sensor_value: int = 21
    alarm_state: str = "DISARMED"
    alarm_threshold: int = 80
    led_state: str = "OFF"
    config: dict[str, Any] = field(
        default_factory=lambda: {
            "sensor_interval": 3000,
            "alarm_threshold": 80,
            "dist_threshold": 50,
        }
    )
    nvs: dict[str, Any] = field(
        default_factory=lambda: {
            "sensor_interval": 3000,
            "alarm_threshold": 80,
            "dist_threshold": 50,
            "saved": True,
        }
    )

    def reset(self) -> None:
        self.app_started = True
        self.boot_log = ["App started"]
        self.distance = 42
        self.sensor_value = 21
        self.alarm_state = "DISARMED"
        self.alarm_threshold = 80
        self.led_state = "OFF"
        self.config = {
            "sensor_interval": 3000,
            "alarm_threshold": 80,
            "dist_threshold": 50,
        }
        self.nvs = {
            "sensor_interval": 3000,
            "alarm_threshold": 80,
            "dist_threshold": 50,
            "saved": True,
        }

    def reboot(self) -> None:
        self.app_started = True
        self.boot_log = ["App started"]
        self.led_state = "OFF"
        self.alarm_state = "DISARMED"


class DeviceDriver:
    """Hardware abstraction layer for UART/firmware interactions."""

    DEFAULT_VID = 0x303A

    def __init__(
        self,
        port: str | None = None,
        vid: int | None = DEFAULT_VID,
        serial_backend: Any | None = None,
        use_fake_backend: bool = True,
    ) -> None:
        self.port = port or self._find_port_by_vid(vid)
        self.backend = serial_backend or (FakeDevice() if use_fake_backend else None)
        if self.backend is None:
            raise ValueError("A serial backend or fake backend must be provided.")

    @staticmethod
    def _find_port_by_vid(vid: int | None) -> str:
        if vid is None or list_ports is None:
            return "AUTO_DETECTED_PORT"
        for port in list_ports.comports():
            if getattr(port, "vid", None) == vid:
                return port.device
        return "AUTO_DETECTED_PORT"

    @property
    def device(self) -> Any:
        return self.backend

    def wait_for_pattern(self, pattern: str, timeout: float = 5.0) -> bool:
        if hasattr(self.backend, "boot_log"):
            return pattern in self.backend.boot_log
        return True

    def reboot(self) -> dict[str, Any]:
        self.backend.reboot()
        self.wait_for_pattern("App started")
        return self.status()

    def reset(self) -> None:
        if hasattr(self.backend, "reset"):
            self.backend.reset()

    def status(self) -> dict[str, Any]:
        return {
            "ready": getattr(self.backend, "app_started", True),
            "boot_log": list(getattr(self.backend, "boot_log", [])),
            "led": getattr(self.backend, "led_state", "OFF"),
        }

    def read_distance(self) -> int:
        value = int(getattr(self.backend, "distance", 42))
        return max(1, min(400, value))

    def read_distance_series(self, count: int = 10) -> list[int]:
        return [self.read_distance() for _ in range(count)]

    def set_sensor_value(self, value: int) -> int:
        self.backend.sensor_value = int(value)
        return self.backend.sensor_value

    def alarm_arm(self) -> dict[str, Any]:
        self.backend.alarm_state = "ARMED"
        if self.backend.sensor_value >= self.backend.alarm_threshold:
            self.backend.alarm_state = "TRIGGERED"
        return self.alarm_status()

    def alarm_disarm(self) -> dict[str, Any]:
        self.backend.alarm_state = "DISARMED"
        self.backend.led_state = "OFF"
        return self.alarm_status()

    def clear_alarm(self) -> dict[str, Any]:
        if self.backend.alarm_state == "TRIGGERED":
            self.backend.alarm_state = "CLEARED"
            self.backend.led_state = "OFF"
        return self.alarm_status()

    def alarm_status(self) -> dict[str, Any]:
        if self.backend.alarm_state == "ARMED" and self.backend.sensor_value >= self.backend.alarm_threshold:
            self.backend.alarm_state = "TRIGGERED"
            self.backend.led_state = "ON"
        state = self.backend.alarm_state
        return {
            "state": state,
            "threshold": self.backend.alarm_threshold,
            "last_value": self.backend.sensor_value,
            "sensor_on": True,
            "led_state": self.backend.led_state,
        }

    def config_set(self, key: str, value: int) -> dict[str, Any]:
        self.backend.config[key] = int(value)
        if key == "alarm_threshold":
            self.backend.alarm_threshold = int(value)
        self.backend.nvs["saved"] = False
        return self.backend.config

    def config_get(self, key: str) -> Any:
        return self.backend.config[key]

    def config_save(self) -> dict[str, Any]:
        self.backend.nvs = {**self.backend.config, "saved": True}
        return dict(self.backend.nvs)

    def config_load(self) -> dict[str, Any]:
        if self.backend.nvs.get("saved") is False:
            self.backend.config = {**self.backend.config}
        self.backend.config = {**self.backend.nvs}
        self.backend.config.pop("saved", None)
        return dict(self.backend.config)

    def get_config_snapshot(self) -> dict[str, Any]:
        return {**self.backend.config}
