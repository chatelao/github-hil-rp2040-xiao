"""Tests for Phase 2 data models and interface definitions."""

import pytest

from xiao_flasher.discovery import IDeviceManagement
from xiao_flasher.flasher import IFirmwareTransport
from xiao_flasher.models import DeviceInfo, FlashResult
from xiao_flasher.telemetry import ITelemetryLog


def test_device_info_dataclass() -> None:
    """Test DeviceInfo dataclass fields and defaults."""
    dev = DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003, port="/dev/ttyACM0")
    assert dev.mode == "RUNTIME"
    assert dev.vid == 0x288A
    assert dev.pid == 0x0003
    assert dev.port == "/dev/ttyACM0"
    assert dev.mount_point is None
    assert dev.serial_number is None


def test_flash_result_dataclass() -> None:
    """Test FlashResult dataclass fields and defaults."""
    res = FlashResult(success=True, bytes_written=1024, duration_seconds=1.5)
    assert res.success is True
    assert res.bytes_written == 1024
    assert res.duration_seconds == 1.5
    assert res.error_message is None

    res_err = FlashResult(
        success=False, bytes_written=0, duration_seconds=0.1, error_message="Failed"
    )
    assert res_err.success is False
    assert res_err.error_message == "Failed"


def test_interfaces_cannot_be_instantiated() -> None:
    """Test abstract base classes cannot be directly instantiated."""
    with pytest.raises(TypeError):
        IDeviceManagement()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IFirmwareTransport()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        ITelemetryLog()  # type: ignore[abstract]


def test_concrete_implementations() -> None:
    """Test concrete subclasses implementing the abstract interfaces."""

    class MockDeviceManagement(IDeviceManagement):
        def find_devices(self) -> list[DeviceInfo]:
            return [DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003)]

        def reset_to_bootsel(
            self, device: DeviceInfo, timeout: float = 10.0
        ) -> DeviceInfo:
            return DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003)

    class MockFirmwareTransport(IFirmwareTransport):
        def validate_firmware(self, file_path: str) -> bool:
            return True

        def flash_uf2(
            self,
            file_path: str,
            target_device: DeviceInfo,
            use_picotool: bool = False,
            verify: bool = True,
            verify_timeout: float = 10.0,
        ) -> FlashResult:
            return FlashResult(success=True, bytes_written=512, duration_seconds=0.5)

    class MockTelemetryLog(ITelemetryLog):
        def __init__(self) -> None:
            self.logs: list[str] = []

        def log_info(self, message: str) -> None:
            self.logs.append(f"INFO: {message}")

        def log_error(self, message: str, error: Exception | None = None) -> None:
            self.logs.append(f"ERROR: {message}")

        def generate_github_summary(
            self, result: FlashResult, device: DeviceInfo
        ) -> None:
            self.logs.append(f"SUMMARY: {result.success}")

    dm = MockDeviceManagement()
    devs = dm.find_devices()
    assert len(devs) == 1
    bootsel_dev = dm.reset_to_bootsel(devs[0])
    assert bootsel_dev.mode == "BOOTSEL"

    ft = MockFirmwareTransport()
    assert ft.validate_firmware("fw.uf2") is True
    res = ft.flash_uf2("fw.uf2", bootsel_dev)
    assert res.success is True

    telemetry = MockTelemetryLog()
    telemetry.log_info("Starting")
    telemetry.log_error("Oops")
    telemetry.generate_github_summary(res, bootsel_dev)
    assert len(telemetry.logs) == 3
