"""Unit tests for TelemetryLogger in xiao_flasher.telemetry."""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from xiao_flasher.models import DeviceInfo, FlashResult
from xiao_flasher.telemetry import TelemetryLogger


def test_telemetry_logger_console_info() -> None:
    """Test console log_info with ANSI and non-ANSI formatting."""
    stream_ansi = io.StringIO()
    logger_ansi = TelemetryLogger(use_ansi=True, stream=stream_ansi)
    logger_ansi.log_info("Test info message")
    assert "\033[32m[INFO]\033[0m Test info message\n" in stream_ansi.getvalue()

    stream_plain = io.StringIO()
    logger_plain = TelemetryLogger(use_ansi=False, stream=stream_plain)
    logger_plain.log_info("Test info message")
    assert "[INFO] Test info message\n" in stream_plain.getvalue()


def test_telemetry_logger_console_error() -> None:
    """Test console log_error with optional exception details and streams."""
    err_stream = io.StringIO()
    logger = TelemetryLogger(use_ansi=True, error_stream=err_stream)
    logger.log_error("Operation failed")
    assert "\033[31m[ERROR]\033[0m Operation failed\n" in err_stream.getvalue()

    err_stream_exc = io.StringIO()
    logger_exc = TelemetryLogger(use_ansi=False, error_stream=err_stream_exc)
    logger_exc.log_error("Write failed", ValueError("Disk full"))
    assert "[ERROR] Write failed (Error: Disk full)\n" in err_stream_exc.getvalue()


def test_generate_github_summary_no_env(tmp_path: Path) -> None:
    """Test generate_github_summary when GITHUB_STEP_SUMMARY is not set."""
    logger = TelemetryLogger()
    result = FlashResult(success=True, bytes_written=1024, duration_seconds=1.2)
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2")

    with patch.dict("os.environ", {}, clear=True):
        logger.generate_github_summary(result, device)
        # Should complete without error when env var is absent


def test_generate_github_summary_success_and_failure(tmp_path: Path) -> None:
    """Test generate_github_summary when GITHUB_STEP_SUMMARY env var is present."""
    summary_file = tmp_path / "step_summary.md"
    logger = TelemetryLogger()

    res_ok = FlashResult(success=True, bytes_written=2048, duration_seconds=2.5)
    dev_ok = DeviceInfo(
        mode="BOOTSEL",
        vid=0x2E8A,
        pid=0x0003,
        port="/dev/ttyACM0",
        mount_point="/media/RPI-RP2",
        serial_number="ABC12345",
    )

    with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}):
        logger.generate_github_summary(res_ok, dev_ok)

        content = summary_file.read_text(encoding="utf-8")
        assert "### XIAO-RP2040 Firmware Flash Summary" in content
        assert "✅ Succeeded" in content
        assert "Bytes Written**: 2048" in content
        assert "Duration**: 2.50 seconds" in content
        assert "Device Mode**: BOOTSEL" in content
        assert "`0x2e8a:0x0003`" in content
        assert "Port**: `/dev/ttyACM0`" in content
        assert "Mount Point**: `/media/RPI-RP2`" in content
        assert "Serial Number**: `ABC12345`" in content

    res_fail = FlashResult(
        success=False, bytes_written=0, duration_seconds=0.5, error_message="Transfer timeout"
    )
    dev_fail = DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003, port="/dev/ttyACM0")

    with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}):
        logger.generate_github_summary(res_fail, dev_fail)

        content_updated = summary_file.read_text(encoding="utf-8")
        assert "❌ Failed" in content_updated
        assert "Error Message**: Transfer timeout" in content_updated


def test_generate_github_summary_os_error(tmp_path: Path) -> None:
    """Test generate_github_summary handles OSError gracefully when writing fails."""
    err_stream = io.StringIO()
    logger = TelemetryLogger(use_ansi=False, error_stream=err_stream)
    result = FlashResult(success=True, bytes_written=1024, duration_seconds=1.0)
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003)

    summary_file = tmp_path / "summary.md"

    with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}), patch(
        "builtins.open", side_effect=OSError("Permission denied")
    ):
        logger.generate_github_summary(result, device)
        assert "[ERROR] Failed to write GitHub Actions step summary: Permission denied\n" in err_stream.getvalue()


def test_export_json(tmp_path: Path) -> None:
    """Test exporting structured JSON report."""
    json_path = tmp_path / "reports" / "summary.json"
    logger = TelemetryLogger()

    res = FlashResult(success=True, bytes_written=4096, duration_seconds=1.8)
    dev = DeviceInfo(
        mode="BOOTSEL",
        vid=0x2E8A,
        pid=0x0003,
        mount_point="/media/RPI-RP2",
        serial_number="XYZ789",
    )

    logger.export_json(json_path, res, dev)

    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))

    assert data["result"]["success"] is True
    assert data["result"]["bytes_written"] == 4096
    assert data["result"]["duration_seconds"] == 1.8
    assert data["result"]["error_message"] is None

    assert data["device"]["mode"] == "BOOTSEL"
    assert data["device"]["vid"] == "0x2e8a"
    assert data["device"]["pid"] == "0x0003"
    assert data["device"]["mount_point"] == "/media/RPI-RP2"
    assert data["device"]["serial_number"] == "XYZ789"
    assert data["device"]["port"] is None


def test_collect_serial_data_success(tmp_path: Path) -> None:
    """Test collect_serial_data reading serial lines and archiving to zip file."""
    zip_path = tmp_path / "test_serial.zip"
    logger = TelemetryLogger(use_ansi=False)

    mock_serial = MagicMock()
    mock_serial.__enter__.return_value = mock_serial
    mock_serial.in_waiting = True
    mock_serial.readline.side_effect = [b"Hello World\n", b"Sensor data: 42\n", b""]

    with patch("serial.Serial", return_value=mock_serial):
        out_path = logger.collect_serial_data(
            port="/dev/ttyACM0",
            duration=0.1,
            zip_output_path=zip_path,
        )

    assert out_path == zip_path
    assert zip_path.exists()

    with zipfile.ZipFile(zip_path, "r") as zf:
        file_list = zf.namelist()
        assert "serial_output.log" in file_list
        log_content = zf.read("serial_output.log").decode("utf-8")
        assert "Hello World" in log_content
        assert "Sensor data: 42" in log_content


def test_collect_serial_data_serial_exception(tmp_path: Path) -> None:
    """Test collect_serial_data when serial port error occurs."""
    zip_path = tmp_path / "error_serial.zip"
    err_stream = io.StringIO()
    logger = TelemetryLogger(use_ansi=False, error_stream=err_stream)

    with patch("serial.Serial", side_effect=Exception("Serial port disconnected")):
        out_path = logger.collect_serial_data(
            port="/dev/ttyACM0",
            duration=0.1,
            zip_output_path=zip_path,
        )

    assert out_path == zip_path
    assert zip_path.exists()
    assert "[ERROR] Error reading serial port /dev/ttyACM0: Serial port disconnected" in err_stream.getvalue()
