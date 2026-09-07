"""Firmware transport interface and implementation for validating and flashing UF2 binaries."""

import os
import shutil
import struct
import subprocess
import time
from abc import ABC, abstractmethod

from xiao_flasher.models import DeviceInfo, FlashResult

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
FLAG_FAMILY_ID_PRESENT = 0x00002000
RP2040_FAMILY_ID = 0xE48DBA66
UF2_BLOCK_SIZE = 512


class IFirmwareTransport(ABC):
    """Abstract base class for firmware validation and transport operations."""

    @abstractmethod
    def validate_firmware(self, file_path: str) -> bool:
        """Validate whether the firmware file format and header are valid for target."""

    @abstractmethod
    def flash_uf2(
        self,
        file_path: str,
        target_device: DeviceInfo,
        use_picotool: bool = False,
        verify: bool = True,
        verify_timeout: float = 10.0,
    ) -> FlashResult:
        """Flash UF2 firmware binary to the target device."""


class UF2Flasher(IFirmwareTransport):
    """Concrete implementation of UF2 firmware validation and transport flasher."""

    def validate_firmware(self, file_path: str) -> bool:
        """Validate UF2 binary format and RP2040 family ID header."""
        if not os.path.isfile(file_path):
            return False

        file_size = os.path.getsize(file_path)
        if file_size < UF2_BLOCK_SIZE or file_size % UF2_BLOCK_SIZE != 0:
            return False

        try:
            with open(file_path, "rb") as f:
                block = f.read(UF2_BLOCK_SIZE)

            if len(block) < UF2_BLOCK_SIZE:
                return False

            (
                magic0,
                magic1,
                flags,
                _target_addr,
                _payload_size,
                _block_num,
                _num_blocks,
                family_id,
            ) = struct.unpack("<IIIIIIII", block[:32])

            (magic_end,) = struct.unpack("<I", block[508:512])

            if (
                magic0 != UF2_MAGIC_START0
                or magic1 != UF2_MAGIC_START1
                or magic_end != UF2_MAGIC_END
            ):
                return False

            return not (flags & FLAG_FAMILY_ID_PRESENT and family_id != RP2040_FAMILY_ID)
        except Exception:  # noqa: BLE001
            return False

    def verify_post_flash(
        self, target_device: DeviceInfo, timeout: float = 10.0
    ) -> bool:
        """Verify volume unmount / state transition following UF2 copy."""
        if not target_device.mount_point:
            return True

        start = time.time()
        while time.time() - start < timeout:
            if not os.path.exists(target_device.mount_point):
                return True
            time.sleep(0.2)

        return not os.path.exists(target_device.mount_point)

    def flash_uf2(
        self,
        file_path: str,
        target_device: DeviceInfo,
        use_picotool: bool = False,
        verify: bool = True,
        verify_timeout: float = 10.0,
    ) -> FlashResult:
        """Flash UF2 firmware binary to the target device via mount point or picotool."""
        start_time = time.time()

        if not self.validate_firmware(file_path):
            return FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=0.0,
                error_message=f"Invalid UF2 firmware or non-RP2040 binary: {file_path}",
            )

        file_size = os.path.getsize(file_path)

        if use_picotool or not target_device.mount_point:
            return self._flash_via_picotool(file_path, target_device, file_size, start_time)

        try:
            mount_path = target_device.mount_point
            if not os.path.isdir(mount_path):
                return FlashResult(
                    success=False,
                    bytes_written=0,
                    duration_seconds=time.time() - start_time,
                    error_message=f"Mount point does not exist or is not a directory: {mount_path}",
                )

            dest_path = shutil.copy(file_path, mount_path)
            if os.path.exists(dest_path):
                # Flush OS file buffers
                try:
                    fd = os.open(dest_path, os.O_WRONLY)
                    os.fsync(fd)
                    os.close(fd)
                except Exception:  # noqa: S110, BLE001
                    pass

            if verify:
                verified = self.verify_post_flash(target_device, timeout=verify_timeout)
                if not verified:
                    return FlashResult(
                        success=False,
                        bytes_written=file_size,
                        duration_seconds=time.time() - start_time,
                        error_message="Post-flash verification failed: volume did not unmount within timeout.",
                    )

            duration = time.time() - start_time
            return FlashResult(
                success=True,
                bytes_written=file_size,
                duration_seconds=duration,
                error_message=None,
            )
        except Exception as err:  # noqa: BLE001
            duration = time.time() - start_time
            return FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=duration,
                error_message=f"Failed to copy UF2 file to volume: {err}",
            )

    def _flash_via_picotool(
        self,
        file_path: str,
        target_device: DeviceInfo,
        file_size: int,
        start_time: float,
    ) -> FlashResult:
        """Fallback flashing using picotool binary utility."""
        if not shutil.which("picotool"):
            return FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=time.time() - start_time,
                error_message="picotool utility not found in system PATH and no mount point available.",
            )

        cmd = ["picotool", "load", "-x", file_path]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = time.time() - start_time
            return FlashResult(
                success=True,
                bytes_written=file_size,
                duration_seconds=duration,
                error_message=None,
            )
        except subprocess.CalledProcessError as err:
            duration = time.time() - start_time
            err_msg = err.stderr.strip() if err.stderr else str(err)
            return FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=duration,
                error_message=f"picotool execution failed: {err_msg}",
            )
