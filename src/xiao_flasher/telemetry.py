"""Telemetry and logging interface for CLI, GitHub Actions, and structured reports."""

import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

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

    @abstractmethod
    def export_json(
        self, output_path: str | Path, result: FlashResult, device: DeviceInfo
    ) -> None:
        """Export structured JSON execution summary to file."""


class TelemetryLogger(ITelemetryLog):
    """Concrete telemetry and logging manager for console output, GitHub Actions summaries, and JSON reports."""

    def __init__(
        self,
        use_ansi: bool = True,
        stream: TextIO | None = None,
        error_stream: TextIO | None = None,
    ) -> None:
        self.use_ansi = use_ansi
        self.stream = stream
        self.error_stream = error_stream

    def _get_stream(self) -> TextIO:
        return self.stream if self.stream is not None else sys.stdout

    def _get_error_stream(self) -> TextIO:
        if self.error_stream is not None:
            return self.error_stream
        if self.stream is not None:
            return self.stream
        return sys.stderr

    def log_info(self, message: str) -> None:
        """Log an informational message."""
        stream = self._get_stream()
        if self.use_ansi:
            formatted = f"\033[32m[INFO]\033[0m {message}"
        else:
            formatted = f"[INFO] {message}"
        stream.write(formatted + "\n")
        stream.flush()

    def log_error(self, message: str, error: Exception | None = None) -> None:
        """Log an error message and optional exception."""
        stream = self._get_error_stream()
        err_msg = f"{message} (Error: {error})" if error else message
        if self.use_ansi:
            formatted = f"\033[31m[ERROR]\033[0m {err_msg}"
        else:
            formatted = f"[ERROR] {err_msg}"
        stream.write(formatted + "\n")
        stream.flush()

    def generate_github_summary(self, result: FlashResult, device: DeviceInfo) -> None:
        """Generate GitHub Actions step summary report in $GITHUB_STEP_SUMMARY file if available."""
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_file:
            return

        status_str = "✅ Succeeded" if result.success else "❌ Failed"
        lines = [
            "### XIAO-RP2040 Firmware Flash Summary",
            "",
            f"- **Status**: {status_str}",
            f"- **Bytes Written**: {result.bytes_written}",
            f"- **Duration**: {result.duration_seconds:.2f} seconds",
            f"- **Device Mode**: {device.mode}",
            f"- **VID:PID**: `0x{device.vid:04x}:0x{device.pid:04x}`",
        ]

        if device.port:
            lines.append(f"- **Port**: `{device.port}`")
        if device.mount_point:
            lines.append(f"- **Mount Point**: `{device.mount_point}`")
        if device.serial_number:
            lines.append(f"- **Serial Number**: `{device.serial_number}`")
        if result.error_message:
            lines.append(f"- **Error Message**: {result.error_message}")

        lines.append("")
        summary_content = "\n".join(lines)

        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(summary_content)
        except OSError as e:
            self.log_error(f"Failed to write GitHub Actions step summary: {e}")

    def export_json(
        self, output_path: str | Path, result: FlashResult, device: DeviceInfo
    ) -> None:
        """Export structured JSON execution summary to file."""
        data = {
            "result": {
                "success": result.success,
                "bytes_written": result.bytes_written,
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
            },
            "device": {
                "mode": device.mode,
                "vid": f"0x{device.vid:04x}" if device.vid is not None else None,
                "pid": f"0x{device.pid:04x}" if device.pid is not None else None,
                "port": device.port,
                "mount_point": device.mount_point,
                "serial_number": device.serial_number,
            },
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
