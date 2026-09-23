from __future__ import annotations

import time
import re
from dataclasses import dataclass, field
from typing import Any

try:
    import serial
except ImportError:  # pragma: no cover
    serial = None

try:
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    list_ports = None


@dataclass
class FakeDevice:
    """In-memory model used as a fallback for CI; production transport is UART."""

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

    def wait_for_pattern(self, pattern: str, timeout: float = 5.0) -> bool:
        return pattern in self.boot_log


class SerialTransport:
    """Real UART transport used against the ESP32-S3 firmware when connected."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.5) -> None:
        if serial is None:
            raise RuntimeError("pyserial is required for real UART transport.")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def send(self, command: str) -> None:
        payload = (command + "\n").encode("utf-8")
        self.serial.write(payload)
        self.serial.flush()

    def wait_for_pattern(self, pattern: str, timeout: float = 5.0) -> str:
        deadline = time.monotonic() + timeout
        buffer = ""
        while time.monotonic() < deadline:
            chunk = self.serial.read(1)
            if not chunk:
                continue
            buffer += chunk.decode("utf-8", errors="ignore")
            if pattern in buffer:
                return buffer
        raise TimeoutError(f"Pattern '{pattern}' was not observed on {self.port}")

    def execute(self, command: str, timeout: float = 10.0) -> str:
        self.serial.reset_input_buffer()
        self.send(command)
        return self.wait_for_pattern("device>", timeout)

    def close(self) -> None:
        if self.serial.is_open:
            self.serial.close()


class DeviceDriver:
    """Hardware abstraction layer with real serial transport and a mock fallback for CI."""

    DEFAULT_VID = 0x1A86

    def __init__(
        self,
        port: str | None = None,
        vid: int | None = DEFAULT_VID,
        serial_backend: Any | None = None,
        use_fake_backend: bool = False,
        transport: str = "auto",
    ) -> None:
        self.transport = transport
        self.port = port or self._find_port_by_vid(vid)
        self._credentials: tuple[str, str] | None = None
        self.backend = self._build_backend(serial_backend, use_fake_backend)

    def _build_backend(self, serial_backend: Any | None, use_fake_backend: bool) -> Any:
        if serial_backend is not None:
            return serial_backend
        detected_port = self.port if self.port and self.port != "AUTO_DETECTED_PORT" else None
        if use_fake_backend or self.transport == "mock":
            return FakeDevice()
        if self.transport in {"serial", "auto"} and detected_port is not None and serial is not None:
            return SerialTransport(detected_port)
        raise RuntimeError("ESP32-S3 UART adapter was not found by VID.")

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
        if hasattr(self.backend, "wait_for_pattern"):
            try:
                self.backend.wait_for_pattern(pattern, timeout)
                return True
            except (AttributeError, TimeoutError, TypeError):
                return False
        if hasattr(self.backend, "boot_log"):
            return pattern in self.backend.boot_log
        return True

    def reboot(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("reboot", timeout=15.0)
            if "Device ready" not in response:
                raise RuntimeError(f"Firmware did not restart correctly: {response.strip()}")
            return {"ready": True, "boot_log": [], "led": "UNKNOWN"}
        else:
            self.backend.reboot()
            self.wait_for_pattern("App started")
        return self.status()

    def reset(self) -> None:
        if hasattr(self.backend, "reset"):
            self.backend.reset()

    def register(self, login: str, password: str) -> None:
        if not isinstance(self.backend, SerialTransport):
            return
        response = self.backend.execute(f"register {login} {password}")
        if "Profile Created" not in response:
            raise RuntimeError(f"Profile registration failed: {response.strip()}")

    def login(self, login: str, password: str) -> None:
        if not isinstance(self.backend, SerialTransport):
            return
        response = self.backend.execute(f"login {login} {password}")
        if "Session Started" not in response:
            raise RuntimeError(f"Authentication failed: {response.strip()}")
        self._credentials = (login, password)

    def restore_session(self) -> None:
        if not isinstance(self.backend, SerialTransport):
            return
        if self._credentials is None:
            raise RuntimeError("No credentials are available to restore the session.")
        login, password = self._credentials
        self.register(login, password)
        self.login(login, password)

    def sensor_start(self) -> None:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute("sensor start")

    def sensor_stop(self) -> None:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute("sensor stop")

    def close(self) -> None:
        if isinstance(self.backend, SerialTransport):
            self.backend.close()

    def status(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("status")
            led_match = re.search(r"LED\s+\(GPIO4\):\s+(ON|OFF)", response)
            return {
                "ready": "[Status] Done." in response,
                "boot_log": [],
                "led": led_match.group(1) if led_match else "UNKNOWN",
            }
        return {
            "ready": getattr(self.backend, "app_started", True),
            "boot_log": list(getattr(self.backend, "boot_log", [])),
            "led": getattr(self.backend, "led_state", "OFF"),
        }

    def read_distance(self) -> int:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("distance")
            match = re.search(r"(?:Distance|#\d+)\D+(\d+(?:\.\d+)?)\s*cm", response)
            if match is None:
                raise RuntimeError(f"Distance reading failed: {response.strip()}")
            return round(float(match.group(1)))
        value = int(getattr(self.backend, "distance", 42))
        return max(1, min(400, value))

    def read_distance_series(self, count: int = 10) -> list[int]:
        return [self.read_distance() for _ in range(count)]

    def set_sensor_value(self, value: int) -> int:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute(f"sensor set {int(value)}")
            return int(value)
        self.backend.sensor_value = int(value)
        return self.backend.sensor_value

    def set_alarm_threshold(self, threshold: int) -> int:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute(f"config set alarm_threshold {int(threshold)}")
            return int(threshold)
        self.backend.alarm_threshold = int(threshold)
        return self.backend.alarm_threshold

    def alarm_arm(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute("alarm arm")
            return self.alarm_status()
        self.backend.alarm_state = "ARMED"
        if self.backend.sensor_value >= self.backend.alarm_threshold:
            self.backend.alarm_state = "TRIGGERED"
        return self.alarm_status()

    def alarm_disarm(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute("alarm disarm")
            return self.alarm_status()
        self.backend.alarm_state = "DISARMED"
        self.backend.led_state = "OFF"
        return self.alarm_status()

    def clear_alarm(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute("alarm clear")
            return self.alarm_status()
        if self.backend.alarm_state == "TRIGGERED":
            self.backend.alarm_state = "CLEARED"
            self.backend.led_state = "OFF"
        return self.alarm_status()

    def alarm_status(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("alarm status")
            fields = {
                "state": r"State:\s+(\w+)",
                "threshold": r"Threshold:\s+(\d+)",
                "last_value": r"Last value:\s+(\d+)",
                "sensor_on": r"Sensor:\s+(running)",
                "led_state": r"LED state:\s+(ON|OFF)",
            }
            values: dict[str, Any] = {}
            for key, pattern in fields.items():
                match = re.search(pattern, response)
                values[key] = match.group(1) if match else None
            if values["state"] is None or values["threshold"] is None:
                raise RuntimeError(f"Could not parse alarm status: {response.strip()}")
            values["threshold"] = int(values["threshold"])
            values["last_value"] = int(values["last_value"] or 0)
            values["sensor_on"] = values["sensor_on"] == "running"
            return values
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

    def wait_for_alarm_state(self, expected_state: str, timeout: float = 5.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        status = self.alarm_status()
        while status["state"] != expected_state and time.monotonic() < deadline:
            status = self.alarm_status()
        return status

    def config_set(self, key: str, value: int) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            self.backend.execute(f"config set {key} {int(value)}")
            return {key: int(value)}
        self.backend.config[key] = int(value)
        if key == "alarm_threshold":
            self.backend.alarm_threshold = int(value)
        self.backend.nvs["saved"] = False
        return self.backend.config

    def config_get(self, key: str) -> Any:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute(f"config get {key}")
            match = re.search(rf"{re.escape(key)}\s*=\s*(\d+)", response)
            if match is None:
                raise RuntimeError(f"Could not parse config '{key}': {response.strip()}")
            return int(match.group(1))
        return self.backend.config[key]

    def config_save(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("config save")
            if "Saved successfully." not in response:
                raise RuntimeError(f"Config save failed: {response.strip()}")
            return {"saved": True}
        self.backend.nvs = {**self.backend.config, "saved": True}
        return dict(self.backend.nvs)

    def config_load(self) -> dict[str, Any]:
        if isinstance(self.backend, SerialTransport):
            response = self.backend.execute("config load")
            return {"saved": "No saved config" not in response}
        if self.backend.nvs.get("saved") is False:
            self.backend.config = {**self.backend.config}
        self.backend.config = {**self.backend.nvs}
        self.backend.config.pop("saved", None)
        return dict(self.backend.config)

    def get_config_snapshot(self) -> dict[str, Any]:
        return {**self.backend.config}
