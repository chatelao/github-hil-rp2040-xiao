"""Data models for xiao_flasher."""

from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Information about a connected XIAO-RP2040 device."""

    mode: str
    vid: int
    pid: int
    port: str | None = None
    mount_point: str | None = None
    serial_number: str | None = None


@dataclass
class FlashResult:
    """Result of a firmware flashing operation."""

    success: bool
    bytes_written: int
    duration_seconds: float
    error_message: str | None = None
