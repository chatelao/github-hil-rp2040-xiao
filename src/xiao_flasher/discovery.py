"""Device management interface for device discovery and state control."""

from abc import ABC, abstractmethod

from xiao_flasher.models import DeviceInfo


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
