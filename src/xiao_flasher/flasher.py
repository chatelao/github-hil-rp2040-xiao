"""Firmware transport interface for validating and flashing firmware binaries."""

from abc import ABC, abstractmethod

from xiao_flasher.models import DeviceInfo, FlashResult


class IFirmwareTransport(ABC):
    """Abstract base class for firmware validation and transport operations."""

    @abstractmethod
    def validate_firmware(self, file_path: str) -> bool:
        """Validate whether the firmware file format and header are valid for target."""
        pass

    @abstractmethod
    def flash_uf2(self, file_path: str, target_device: DeviceInfo) -> FlashResult:
        """Flash UF2 firmware binary to the target device."""
        pass
