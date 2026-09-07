"""Telemetry and logging interface for CLI, GitHub Actions, and structured reports."""

from abc import ABC, abstractmethod
from typing import Optional

from xiao_flasher.models import DeviceInfo, FlashResult


class ITelemetryLog(ABC):
    """Abstract base class for telemetry and execution logging."""

    @abstractmethod
    def log_info(self, message: str) -> None:
        """Log an informational message."""
        pass

    @abstractmethod
    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error message and optional exception."""
        pass

    @abstractmethod
    def generate_github_summary(self, result: FlashResult, device: DeviceInfo) -> None:
        """Generate GitHub Actions step summary report."""
        pass
