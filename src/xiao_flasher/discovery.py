"""Device management interface and implementation for device discovery and state control."""

import time
from abc import ABC, abstractmethod

import psutil
import serial
import serial.tools.list_ports

from xiao_flasher.models import DeviceInfo

SEEED_VID = 0x288A
XIAO_RP2040_CDC_PID = 0x0003

RASPBERRY_PI_VID = 0x2E8A
RP2040_BOOTSEL_PID = 0x0003
BOOTSEL_VOLUME_NAME = "RPI-RP2"


class IDeviceManagement(ABC):
    """Abstract base class for device discovery and state management."""

    @abstractmethod
    def find_devices(self) -> list[DeviceInfo]:
        """Discover connected XIAO-RP2040 devices in runtime or BOOTSEL mode."""

    @abstractmethod
    def reset_to_bootsel(
        self, device: DeviceInfo, timeout: float = 10.0
    ) -> DeviceInfo:
        """Reset a device from runtime mode into BOOTSEL bootloader mode."""


class DeviceManager(IDeviceManagement):
    """Concrete implementation of device discovery and bootloader reset controller."""

    def __init__(
        self,
        runtime_vid: int = SEEED_VID,
        runtime_pid: int = XIAO_RP2040_CDC_PID,
    ) -> None:
        self.runtime_vid = runtime_vid
        self.runtime_pid = runtime_pid

    def find_devices(self) -> list[DeviceInfo]:
        """Discover connected XIAO-RP2040 devices in runtime CDC or BOOTSEL mode."""
        devices: list[DeviceInfo] = []

        # 1. Check CDC Serial ports for Runtime mode
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if (
                p.vid is not None
                and p.pid is not None
                and p.vid == self.runtime_vid
                and p.pid == self.runtime_pid
            ):
                devices.append(
                    DeviceInfo(
                        mode="RUNTIME",
                        vid=p.vid,
                        pid=p.pid,
                        port=p.device,
                        serial_number=p.serial_number,
                    )
                )

        # 2. Check Mounted Volumes for BOOTSEL mode (RPI-RP2)
        partitions = psutil.disk_partitions(all=True)
        for part in partitions:
            # Check partition mount point or device name ending/containing volume label
            mount = part.mountpoint
            opts = part.opts
            # On Linux/macOS mountpoint might end in RPI-RP2, or volume label check
            if BOOTSEL_VOLUME_NAME in mount or BOOTSEL_VOLUME_NAME in opts:
                devices.append(
                    DeviceInfo(
                        mode="BOOTSEL",
                        vid=RASPBERRY_PI_VID,
                        pid=RP2040_BOOTSEL_PID,
                        mount_point=mount,
                    )
                )

        return devices

    def reset_to_bootsel(
        self, device: DeviceInfo, timeout: float = 10.0
    ) -> DeviceInfo:
        """Reset a runtime CDC device into BOOTSEL mode using 1200-baud touch reset."""
        if device.mode == "BOOTSEL":
            return device

        if not device.port:
            raise ValueError("Cannot reset device without a valid serial port.")

        # Trigger 1200-baud rate reset
        try:
            s = serial.Serial(device.port, 1200)
            s.close()
        except Exception:  # noqa: S110, BLE001
            # Port opening/closing to signal reboot may throw port closed error on reset
            pass

        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            found_devices = self.find_devices()
            for dev in found_devices:
                if dev.mode == "BOOTSEL":
                    return dev

        raise TimeoutError(
            f"Timed out after {timeout} seconds waiting for device {device.port} "
            "to re-enumerate in BOOTSEL mode."
        )
