"""Unit tests for DeviceManager in xiao_flasher.discovery."""

from unittest.mock import MagicMock, patch

import pytest

from xiao_flasher.discovery import DeviceManager
from xiao_flasher.models import DeviceInfo


def test_find_devices_runtime_and_bootsel() -> None:
    """Test discovering devices in runtime CDC mode and BOOTSEL mode."""
    mock_port_1 = MagicMock()
    mock_port_1.vid = 0x288A
    mock_port_1.pid = 0x0003
    mock_port_1.device = "/dev/ttyACM0"
    mock_port_1.serial_number = "123456"

    mock_port_2 = MagicMock()
    mock_port_2.vid = 0x1234
    mock_port_2.pid = 0x5678
    mock_port_2.device = "/dev/ttyUSB0"
    mock_port_2.serial_number = None

    mock_part_1 = MagicMock()
    mock_part_1.mountpoint = "/media/user/RPI-RP2"
    mock_part_1.opts = "rw,nosuid,nodev"

    mock_part_2 = MagicMock()
    mock_part_2.mountpoint = "/mnt/data"
    mock_part_2.opts = "rw"

    with patch(
        "serial.tools.list_ports.comports", return_value=[mock_port_1, mock_port_2]
    ), patch("psutil.disk_partitions", return_value=[mock_part_1, mock_part_2]):
        dm = DeviceManager()
        devices = dm.find_devices()

        assert len(devices) == 2

        runtime_dev = next(d for d in devices if d.mode == "RUNTIME")
        assert runtime_dev.vid == 0x288A
        assert runtime_dev.pid == 0x0003
        assert runtime_dev.port == "/dev/ttyACM0"
        assert runtime_dev.serial_number == "123456"

        bootsel_dev = next(d for d in devices if d.mode == "BOOTSEL")
        assert bootsel_dev.vid == 0x2E8A
        assert bootsel_dev.pid == 0x0003
        assert bootsel_dev.mount_point == "/media/user/RPI-RP2"


def test_reset_to_bootsel_already_bootsel() -> None:
    """Test resetting a device that is already in BOOTSEL mode returns immediately."""
    dm = DeviceManager()
    dev = DeviceInfo(
        mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2"
    )
    res = dm.reset_to_bootsel(dev)
    assert res == dev


def test_reset_to_bootsel_missing_port() -> None:
    """Test resetting a RUNTIME device without a port raises ValueError."""
    dm = DeviceManager()
    dev = DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003, port=None)
    with pytest.raises(ValueError, match="Cannot reset device without a valid serial port"):
        dm.reset_to_bootsel(dev)


def test_reset_to_bootsel_success() -> None:
    """Test successful 1200-baud reset state transition."""
    dm = DeviceManager()
    dev = DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003, port="/dev/ttyACM0")

    bootsel_dev = DeviceInfo(
        mode="BOOTSEL", vid=0x2E8A, pid=0x0003, mount_point="/media/RPI-RP2"
    )

    with patch("serial.Serial") as mock_serial, patch.object(
        dm, "find_devices", side_effect=[[], [bootsel_dev]]
    ) as mock_find_devices, patch("time.sleep"):
        res = dm.reset_to_bootsel(dev, timeout=5.0)

        mock_serial.assert_called_once_with("/dev/ttyACM0", 1200)
        assert res == bootsel_dev
        assert mock_find_devices.call_count == 2


def test_reset_to_bootsel_timeout() -> None:
    """Test 1200-baud reset timeout raises TimeoutError."""
    dm = DeviceManager()
    dev = DeviceInfo(mode="RUNTIME", vid=0x288A, pid=0x0003, port="/dev/ttyACM0")

    with patch("serial.Serial"), patch.object(
        dm, "find_devices", return_value=[]
    ), patch("time.sleep"):
        with pytest.raises(TimeoutError, match="Timed out after 0.1 seconds"):
            dm.reset_to_bootsel(dev, timeout=0.1)
