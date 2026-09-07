"""Telemetry and logging interface for CLI, GitHub Actions, and structured reports."""

from abc import ABC, abstractmethod

from xiao_flasher.models import DeviceInfo, FlashResult


class ITelemetryLog(ABC):
    """Abstract base class for telemetry and execution logging."""

    @abstractmethod
    def log_info(self, message: str) -> None:
        """Log an informational message."""

    @abstractmethod
    def log_error(self, message: str, error: Exception | None = None) -> None:
        """Log an error message and optional exception."""

    @abstractmethod
    def generate_github_summary(self, result: FlashResult, device: DeviceInfo) -> None:
        """Generate GitHub Actions step summary report."""
