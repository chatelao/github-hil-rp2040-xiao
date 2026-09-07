"""Unit tests for UF2 firmware transport flasher module."""

import struct
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xiao_flasher.flasher import (
    FLAG_FAMILY_ID_PRESENT,
    RP2040_FAMILY_ID,
    UF2_BLOCK_SIZE,
    UF2_MAGIC_END,
    UF2_MAGIC_START0,
    UF2_MAGIC_START1,
    UF2Flasher,
)
from xiao_flasher.models import DeviceInfo


def make_uf2_block(
    magic0: int = UF2_MAGIC_START0,
    magic1: int = UF2_MAGIC_START1,
    flags: int = FLAG_FAMILY_ID_PRESENT,
    target_addr: int = 0x10000000,
    payload_size: int = 256,
    block_num: int = 0,
    num_blocks: int = 1,
    family_id: int = RP2040_FAMILY_ID,
    magic_end: int = UF2_MAGIC_END,
) -> bytes:
    """Helper to generate a valid 512-byte UF2 block."""
    header = struct.pack(
        "<IIIIIIII",
        magic0,
        magic1,
        flags,
        target_addr,
        payload_size,
        block_num,
        num_blocks,
        family_id,
    )
    payload = b"\x00" * 476
    trailer = struct.pack("<I", magic_end)
    return header + payload + trailer


@pytest.fixture
def valid_uf2_file(tmp_path: Path) -> Path:
    """Create a valid temporary UF2 file for RP2040."""
    file_path = tmp_path / "firmware.uf2"
    block = make_uf2_block()
    file_path.write_bytes(block)
    return file_path


def test_validate_firmware_valid(valid_uf2_file: Path) -> None:
    flasher = UF2Flasher()
    assert flasher.validate_firmware(str(valid_uf2_file)) is True


def test_validate_firmware_nonexistent() -> None:
    flasher = UF2Flasher()
    assert flasher.validate_firmware("/nonexistent/file.uf2") is False


def test_validate_firmware_invalid_size(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    bad_file = tmp_path / "bad_size.uf2"
    bad_file.write_bytes(b"short payload")
    assert flasher.validate_firmware(str(bad_file)) is False


def test_validate_firmware_invalid_magic(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    bad_file = tmp_path / "bad_magic.uf2"
    block = make_uf2_block(magic0=0xDEADBEEF)
    bad_file.write_bytes(block)
    assert flasher.validate_firmware(str(bad_file)) is False


def test_validate_firmware_invalid_family_id(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    bad_file = tmp_path / "bad_family.uf2"
    block = make_uf2_block(family_id=0x12345678)
    bad_file.write_bytes(block)
    assert flasher.validate_firmware(str(bad_file)) is False


def test_validate_firmware_no_family_flag(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    file_path = tmp_path / "no_family_flag.uf2"
    block = make_uf2_block(flags=0x00000000)
    file_path.write_bytes(block)
    assert flasher.validate_firmware(str(file_path)) is True


def test_flash_uf2_invalid_firmware(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    invalid_file = tmp_path / "invalid.uf2"
    invalid_file.write_bytes(b"invalid data")
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=str(tmp_path))

    res = flasher.flash_uf2(str(invalid_file), device)
    assert res.success is False
    assert res.bytes_written == 0
    assert "Invalid UF2 firmware" in (res.error_message or "")


def test_flash_uf2_volume_copy_success(valid_uf2_file: Path, tmp_path: Path) -> None:
    flasher = UF2Flasher()
    mount_dir = tmp_path / "RPI-RP2"
    mount_dir.mkdir()

    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=str(mount_dir))

    # Disable post-flash verification unmount check since test tmp_path dir doesn't auto-unmount
    res = flasher.flash_uf2(str(valid_uf2_file), device, verify=False)
    assert res.success is True
    assert res.bytes_written == UF2_BLOCK_SIZE
    assert res.error_message is None
    assert (mount_dir / "firmware.uf2").exists()


def test_verify_post_flash_unmount(tmp_path: Path) -> None:
    flasher = UF2Flasher()
    mount_dir = tmp_path / "RPI-RP2"
    mount_dir.mkdir()

    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=str(mount_dir))
    # Directory exists -> verify_post_flash times out
    assert flasher.verify_post_flash(device, timeout=0.1) is False

    # Remove directory -> verify_post_flash succeeds
    mount_dir.rmdir()
    assert flasher.verify_post_flash(device, timeout=0.1) is True


def test_flash_uf2_volume_copy_verification_failure(
    valid_uf2_file: Path, tmp_path: Path
) -> None:
    flasher = UF2Flasher()
    mount_dir = tmp_path / "RPI-RP2"
    mount_dir.mkdir()

    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=str(mount_dir))

    res = flasher.flash_uf2(str(valid_uf2_file), device, verify=True, verify_timeout=0.1)
    assert res.success is False
    assert "Post-flash verification failed" in (res.error_message or "")


def test_flash_uf2_volume_copy_nonexistent_mount(valid_uf2_file: Path) -> None:
    flasher = UF2Flasher()
    device = DeviceInfo(
        mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/nonexistent/mount/path"
    )

    res = flasher.flash_uf2(str(valid_uf2_file), device)
    assert res.success is False
    assert "Mount point does not exist" in (res.error_message or "")


@patch("shutil.which")
@patch("subprocess.run")
def test_flash_uf2_picotool_success(
    mock_run: MagicMock, mock_which: MagicMock, valid_uf2_file: Path
) -> None:
    mock_which.return_value = "/usr/bin/picotool"
    mock_run.return_value = subprocess.CompletedProcess(
        args=["picotool", "load", "-x"], returncode=0, stdout="OK", stderr=""
    )

    flasher = UF2Flasher()
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=None)

    res = flasher.flash_uf2(str(valid_uf2_file), device, use_picotool=True)
    assert res.success is True
    assert res.bytes_written == UF2_BLOCK_SIZE
    assert res.error_message is None
    mock_run.assert_called_once_with(
        ["picotool", "load", "-x", str(valid_uf2_file)],
        capture_output=True,
        text=True,
        check=True,
    )


@patch("shutil.which")
def test_flash_uf2_picotool_not_installed(mock_which: MagicMock, valid_uf2_file: Path) -> None:
    mock_which.return_value = None

    flasher = UF2Flasher()
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=None)

    res = flasher.flash_uf2(str(valid_uf2_file), device, use_picotool=True)
    assert res.success is False
    assert "picotool utility not found" in (res.error_message or "")


@patch("shutil.which")
@patch("subprocess.run")
def test_flash_uf2_picotool_failure(
    mock_run: MagicMock, mock_which: MagicMock, valid_uf2_file: Path
) -> None:
    mock_which.return_value = "/usr/bin/picotool"
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["picotool"], stderr="Device not found"
    )

    flasher = UF2Flasher()
    device = DeviceInfo(mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point=None)

    res = flasher.flash_uf2(str(valid_uf2_file), device, use_picotool=True)
    assert res.success is False
    assert "picotool execution failed: Device not found" in (res.error_message or "")
