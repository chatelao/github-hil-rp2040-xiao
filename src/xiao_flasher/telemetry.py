"""Telemetry and logging interface for CLI, GitHub Actions, and structured reports."""

import json
import os
import sys
import time
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

import serial

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

    @abstractmethod
    def collect_serial_data(
        self,
        port: str,
        duration: float = 20.0,
        zip_output_path: str | Path | None = None,
        baudrate: int = 115200,
        chunk_size: int = 1024,
    ) -> Path | None:
        """Collect serial data from port for duration (seconds) and optional zip output."""


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

    def collect_serial_data(
        self,
        port: str,
        duration: float = 20.0,
        zip_output_path: str | Path | None = None,
        baudrate: int = 115200,
        chunk_size: int = 1024,
    ) -> Path | None:
        """Read CDC serial data for specified duration and package into zip archive."""
        self.log_info(
            f"Collecting serial data on port {port} for {duration:.1f}s "
            f"(baudrate={baudrate}, chunk_size={chunk_size})..."
        )
        collected_lines: list[str] = []
        overrun_count = 0
        start_time = time.time()

        try:
            with serial.Serial(port, baudrate=baudrate, timeout=0.5) as ser:
                while time.time() - start_time < duration:
                    in_w = ser.in_waiting
                    if in_w > 0:
                        # Monitor buffer overrun condition
                        if in_w > chunk_size * 4:
                            overrun_count += 1
                            ts_overrun = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                            warning_msg = (
                                f"[{ts_overrun}] [BUFFER OVERRUN WARNING] Unread bytes in buffer: {in_w} bytes\n"
                            )
                            collected_lines.append(warning_msg)
                            self.log_error(f"Buffer overrun detected on {port}: {in_w} unread bytes in buffer.")

                        to_read = min(in_w, chunk_size)
                        raw_data = ser.read(to_read)
                        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                        text_data = raw_data.decode("utf-8", errors="replace")

                        for line in text_data.splitlines(keepends=True):
                            collected_lines.append(f"[{ts}] {line}")
                    else:
                        time.sleep(0.05)
        except Exception as e:  # noqa: BLE001
            self.log_error(f"Error reading serial port {port}: {e}")

        if overrun_count > 0:
            self.log_error(f"Total buffer overrun events detected during collection: {overrun_count}")

        log_content = "".join(collected_lines)
        if not zip_output_path:
            zip_output_path = Path("serial_log.zip")
        else:
            zip_output_path = Path(zip_output_path)

        zip_output_path.parent.mkdir(parents=True, exist_ok=True)
        log_filename = "serial_output.log"

        try:
            with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(log_filename, log_content)
            self.log_info(f"Serial log successfully saved and zipped to {zip_output_path}")
            return zip_output_path
        except Exception as e:  # noqa: BLE001
            self.log_error(f"Failed to create zip archive {zip_output_path}: {e}")
            return None
