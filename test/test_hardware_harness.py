"""Simulated Hardware Test Harness for XIAO-RP2040 state transitions and flashing."""

import shutil
import struct
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from typing_extensions import Self

from xiao_flasher.cli import main
from xiao_flasher.discovery import DeviceManager
from xiao_flasher.flasher import (
    FLAG_FAMILY_ID_PRESENT,
    RP2040_FAMILY_ID,
    UF2_MAGIC_END,
    UF2_MAGIC_START0,
    UF2_MAGIC_START1,
    UF2Flasher,
)


def make_valid_uf2_block() -> bytes:
    """Helper to construct a valid 512-byte UF2 block for RP2040."""
    header = struct.pack(
        "<IIIIIIII",
        UF2_MAGIC_START0,
        UF2_MAGIC_START1,
        FLAG_FAMILY_ID_PRESENT,
        0x10000000,
        256,
        0,
        1,
        RP2040_FAMILY_ID,
    )
    payload = b"\x00" * 476
    trailer = struct.pack("<I", UF2_MAGIC_END)
    return header + payload + trailer


class SimulatedXIAORP2040:
    """Hardware simulator for Seeed Studio XIAO-RP2040 state transitions.

    Simulates CDC serial port runtime mode (1200-baud touch reset) and
    BOOTSEL USB mass storage volume mode with post-flash verification.
    """

    def __init__(self, base_dir: Path, port: str = "/dev/ttyACM0") -> None:
        self.base_dir = base_dir
        self.port = port
        self.state = "RUNTIME"
        self.mount_path = base_dir / "RPI-RP2"
        self.patchers: list[Any] = []
        self.copied_files: list[Path] = []

    def start(self) -> Self:
        """Start hardware patches."""
        self._patch_comports = patch(
            "serial.tools.list_ports.comports", side_effect=self._mock_comports
        )
        self._patch_partitions = patch(
            "psutil.disk_partitions", side_effect=self._mock_partitions
        )
        self._patch_serial = patch("serial.Serial", side_effect=self._mock_serial)
        self._patch_copy = patch("shutil.copy", side_effect=self._mock_copy)

        self.patchers = [
            self._patch_comports,
            self._patch_partitions,
            self._patch_serial,
            self._patch_copy,
        ]
        for p in self.patchers:
            p.start()
        return self

    def stop(self) -> None:
        """Stop hardware patches."""
        for p in self.patchers:
            p.stop()

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(self, *args: object) -> None:
        self.stop()

    def _mock_comports(self) -> list[MagicMock]:
        if self.state == "RUNTIME":
            p = MagicMock()
            p.vid = 0x288A
            p.pid = 0x0003
            p.device = self.port
            p.serial_number = "XIAO2040_SIM"
            return [p]
        return []

    def _mock_partitions(self, all: bool = True) -> list[MagicMock]:
        if self.state == "BOOTSEL" and self.mount_path.exists():
            part = MagicMock()
            part.mountpoint = str(self.mount_path)
            part.opts = "rw,nosuid,nodev"
            return [part]
        return []

    def _mock_serial(self, port: str, baudrate: int = 9600, **kwargs: Any) -> MagicMock:
        if port == self.port and baudrate == 1200:
            # 1200 baud touch reset triggers transition from RUNTIME to BOOTSEL
            self.state = "BOOTSEL"
            if not self.mount_path.exists():
                self.mount_path.mkdir(parents=True, exist_ok=True)
                (self.mount_path / "INFO_UF2.TXT").write_text(
                    "UF2 Bootloader v3.0\nBoard-ID: RPI-RP2\n", encoding="utf-8"
                )
        mock_s = MagicMock()
        mock_s.is_open = True
        return mock_s

    def _mock_copy(self, src: str, dst: str, **kwargs: Any) -> str:
        # Perform real file copy into target dst
        copied = shutil.copy2(src, dst)
        self.copied_files.append(Path(copied))
        # Simulate hardware behavior: upon write completion, device unmounts BOOTSEL volume
        # and re-enumerates back into RUNTIME mode after flashing
        if self.mount_path.exists():
            shutil.rmtree(self.mount_path, ignore_errors=True)
        self.state = "RUNTIME"
        return copied


@pytest.fixture
def hardware_simulator(tmp_path: Path) -> Generator[SimulatedXIAORP2040, None, None]:
    """Pytest fixture yielding an active SimulatedXIAORP2040 hardware instance."""
    sim = SimulatedXIAORP2040(tmp_path)
    with sim:
        yield sim


def test_virtual_serial_1200_baud_touch_reset(
    hardware_simulator: SimulatedXIAORP2040,
) -> None:
    """Test virtual serial port 1200-baud touch reset state transition."""
    dm = DeviceManager()

    # Initial discovery finding device in RUNTIME mode
    devs = dm.find_devices()
    assert len(devs) == 1
    assert devs[0].mode == "RUNTIME"
    assert devs[0].port == "/dev/ttyACM0"

    # Reset device to BOOTSEL mode via 1200-baud baud touch
    bootsel_dev = dm.reset_to_bootsel(devs[0], timeout=2.0)
    assert bootsel_dev.mode == "BOOTSEL"
    assert bootsel_dev.mount_point == str(hardware_simulator.mount_path)
    assert hardware_simulator.state == "BOOTSEL"


def test_mock_bootsel_volume_flash_and_verification(
    hardware_simulator: SimulatedXIAORP2040, tmp_path: Path
) -> None:
    """Test flashing UF2 binary to mock BOOTSEL volume with post-flash unmount verification."""
    # Put hardware simulator directly in BOOTSEL state
    hardware_simulator.state = "BOOTSEL"
    hardware_simulator.mount_path.mkdir(parents=True, exist_ok=True)

    dm = DeviceManager()
    devs = dm.find_devices()
    assert len(devs) == 1
    assert devs[0].mode == "BOOTSEL"

    # Prepare valid UF2 file
    uf2_path = tmp_path / "firmware.uf2"
    uf2_path.write_bytes(make_valid_uf2_block())

    # Flash UF2 and verify post-flash volume unmount
    flasher = UF2Flasher()
    result = flasher.flash_uf2(str(uf2_path), devs[0], verify=True, verify_timeout=2.0)

    assert result.success is True
    assert result.bytes_written == 512
    assert result.error_message is None
    assert hardware_simulator.state == "RUNTIME"


def test_cli_end_to_end_simulated_flashing(
    hardware_simulator: SimulatedXIAORP2040, tmp_path: Path
) -> None:
    """Test full end-to-end CLI workflow using simulated hardware harness."""
    uf2_path = tmp_path / "demo.uf2"
    uf2_path.write_bytes(make_valid_uf2_block())

    json_report_path = tmp_path / "report.json"

    runner = CliRunner()
    cli_res = runner.invoke(
        main,
        [
            "-f",
            str(uf2_path),
            "-p",
            "/dev/ttyACM0",
            "-j",
            str(json_report_path),
            "-t",
            "5.0",
        ],
    )

    assert cli_res.exit_code == 0, f"CLI output: {cli_res.output}"
    assert "Flash operation succeeded!" in cli_res.output
    assert json_report_path.exists()

    report_content = json_report_path.read_text(encoding="utf-8")
    assert '"success": true' in report_content


sketch_uf2_path = (
    Path(__file__).parent / "fixtures" / "sample_sketch" / "build" / "sample_sketch.ino.uf2"
)


@pytest.mark.skipif(
    not sketch_uf2_path.exists(),
    reason="Compiled sample sketch binary not found. Run compile_sample.sh to generate it.",
)
def test_compiled_sample_sketch_uf2_validation() -> None:
    """Validate that the compiled sample sketch UF2 binary meets RP2040 requirements."""
    flasher = UF2Flasher()
    assert flasher.validate_firmware(str(sketch_uf2_path)) is True
