"""Unit tests for xiao-flasher CLI entry point and orchestrator."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from test.test_flasher import make_uf2_block
from xiao_flasher.cli import main
from xiao_flasher.models import DeviceInfo, FlashResult


def create_valid_uf2(tmp_path: Path) -> Path:
    uf2_file = tmp_path / "valid_firmware.uf2"
    block = make_uf2_block()
    uf2_file.write_bytes(block)
    return uf2_file


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "-f, --firmware" in result.output
    assert "-p, --port" in result.output
    assert "-m, --mount" in result.output
    assert "-u, --use-picotool" in result.output
    assert "-v, --verify" in result.output
    assert "-j, --json-output" in result.output
    assert "-t, --timeout" in result.output
    assert "-c, --collect-serial" in result.output
    assert "-d, --duration" in result.output
    assert "-z, --zip-output" in result.output


@patch("xiao_flasher.cli.TelemetryLogger.collect_serial_data")
@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
@patch("xiao_flasher.cli.DeviceManager.reset_to_bootsel")
def test_cli_serial_collection(
    mock_reset: MagicMock, mock_flash: MagicMock, mock_collect: MagicMock, tmp_path: Path
) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    zip_out = tmp_path / "serial.zip"
    bootsel_dev = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, port="/dev/ttyACM0", mount_point="/media/RPI-RP2")
    mock_reset.return_value = bootsel_dev
    mock_flash.return_value = FlashResult(
        success=True, bytes_written=512, duration_seconds=0.1, error_message=None
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-p", "/dev/ttyACM0", "-c", "-d", "15", "-z", str(zip_out)],
    )
    assert result.exit_code == 0
    mock_collect.assert_called_once_with(
        port="/dev/ttyACM0",
        duration=15.0,
        zip_output_path=zip_out,
    )


def test_cli_missing_firmware() -> None:
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code != 0
    assert "Missing option '-f' / '--firmware'" in result.output


def test_cli_invalid_firmware(tmp_path: Path) -> None:
    bad_uf2 = tmp_path / "invalid.uf2"
    bad_uf2.write_bytes(b"invalid header bytes")

    runner = CliRunner()
    result = runner.invoke(main, ["-f", str(bad_uf2)])
    assert result.exit_code == 1
    assert "Invalid UF2 firmware file" in result.output


@patch("xiao_flasher.cli.DeviceManager.find_devices")
def test_cli_no_devices_found(mock_find: MagicMock, tmp_path: Path) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    mock_find.return_value = []

    runner = CliRunner()
    result = runner.invoke(main, ["-f", str(valid_uf2)])
    assert result.exit_code == 1
    assert "No XIAO-RP2040 devices found" in result.output


@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
def test_cli_success_with_mount_option(mock_flash: MagicMock, tmp_path: Path) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    mock_flash.return_value = FlashResult(
        success=True, bytes_written=512, duration_seconds=0.1, error_message=None
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-m", "/media/RPI-RP2", "--no-verify"],
    )
    assert result.exit_code == 0
    assert "Using specified mount point: /media/RPI-RP2" in result.output
    assert "Flash operation succeeded!" in result.output
    mock_flash.assert_called_once()


@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
@patch("xiao_flasher.cli.DeviceManager.reset_to_bootsel")
def test_cli_success_with_port_option_and_reset(
    mock_reset: MagicMock, mock_flash: MagicMock, tmp_path: Path
) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    bootsel_dev = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2")
    mock_reset.return_value = bootsel_dev
    mock_flash.return_value = FlashResult(
        success=True, bytes_written=512, duration_seconds=0.2, error_message=None
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-p", "/dev/ttyACM0", "-v"],
    )
    assert result.exit_code == 0
    assert "Using specified serial port: /dev/ttyACM0" in result.output
    assert "Resetting to BOOTSEL mode..." in result.output
    mock_reset.assert_called_once()
    mock_flash.assert_called_once()


@patch("xiao_flasher.cli.DeviceManager.reset_to_bootsel")
def test_cli_reset_failure(mock_reset: MagicMock, tmp_path: Path) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    mock_reset.side_effect = TimeoutError("Timed out waiting for BOOTSEL")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-p", "/dev/ttyACM0"],
    )
    assert result.exit_code == 1
    assert "Failed to reset device to BOOTSEL mode" in result.output


@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
def test_cli_flash_failure(mock_flash: MagicMock, tmp_path: Path) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    mock_flash.return_value = FlashResult(
        success=False, bytes_written=0, duration_seconds=0.1, error_message="Write error"
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-m", "/media/RPI-RP2"],
    )
    assert result.exit_code == 1
    assert "Flash operation failed: Write error" in result.output


@patch("xiao_flasher.cli.DeviceManager.find_devices")
@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
def test_cli_auto_discovery_multiple_devices(
    mock_flash: MagicMock, mock_find: MagicMock, tmp_path: Path
) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    dev1 = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2-1")
    dev2 = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2-2")
    mock_find.return_value = [dev1, dev2]
    mock_flash.return_value = FlashResult(
        success=True, bytes_written=512, duration_seconds=0.1, error_message=None
    )

    runner = CliRunner()
    result = runner.invoke(main, ["-f", str(valid_uf2)])
    assert result.exit_code == 0
    assert "Multiple devices found. Selecting first device" in result.output


@patch("xiao_flasher.cli.UF2Flasher.flash_uf2")
def test_cli_json_export(mock_flash: MagicMock, tmp_path: Path) -> None:
    valid_uf2 = create_valid_uf2(tmp_path)
    json_path = tmp_path / "out" / "report.json"
    mock_flash.return_value = FlashResult(
        success=True, bytes_written=512, duration_seconds=0.15, error_message=None
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["-f", str(valid_uf2), "-m", "/media/RPI-RP2", "-j", str(json_path)],
    )
    assert result.exit_code == 0
    assert json_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["result"]["success"] is True
    assert data["result"]["bytes_written"] == 512
    assert data["device"]["mount_point"] == "/media/RPI-RP2"
