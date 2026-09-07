"""Data models for xiao_flasher."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceInfo:
    """Information about a connected XIAO-RP2040 device."""

    mode: str
    vid: int
    pid: int
    port: Optional[str] = None
    mount_point: Optional[str] = None
    serial_number: Optional[str] = None


@dataclass
class FlashResult:
    """Result of a firmware flashing operation."""

    success: bool
    bytes_written: int
    duration_seconds: float
    error_message: Optional[str] = None
