"""CLI entry point and workflow orchestrator for xiao-flasher."""

import sys
from pathlib import Path

import click

from xiao_flasher.discovery import (
    RASPBERRY_PI_VID,
    RP2040_BOOTSEL_PID,
    SEEED_VID,
    XIAO_RP2040_CDC_PID,
    DeviceManager,
)
from xiao_flasher.flasher import UF2Flasher
from xiao_flasher.models import DeviceInfo, FlashResult
from xiao_flasher.telemetry import TelemetryLogger


@click.command()
@click.option(
    "-f",
    "--firmware",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to .uf2 firmware file to flash.",
)
@click.option(
    "-p",
    "--port",
    type=str,
    default=None,
    help="Target CDC serial port (e.g. /dev/ttyACM0 or COM3).",
)
@click.option(
    "-m",
    "--mount",
    type=str,
    default=None,
    help="Target BOOTSEL mount point path.",
)
@click.option(
    "-u",
    "--use-picotool",
    is_flag=True,
    default=False,
    help="Use picotool for raw USB flashing fallback.",
)
@click.option(
    "-v/-nv",
    "--verify/--no-verify",
    default=True,
    help="Enable or disable post-flash unmount verification.",
)
@click.option(
    "-j",
    "--json-output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to export structured JSON execution summary.",
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    default=10.0,
    help="Timeout in seconds for device reset and verification.",
)
def main(
    firmware: Path,
    port: str | None,
    mount: str | None,
    use_picotool: bool,
    verify: bool,
    json_output: Path | None,
    timeout: float,
) -> None:
    """XIAO-RP2040 Firmware Flashing CLI."""
    logger = TelemetryLogger()
    flasher = UF2Flasher()
    device_mgr = DeviceManager()

    logger.log_info(f"Starting xiao-flasher for firmware: {firmware}")

    if not flasher.validate_firmware(str(firmware)):
        err_msg = f"Invalid UF2 firmware file: {firmware}"
        logger.log_error(err_msg)
        fail_res = FlashResult(
            success=False,
            bytes_written=0,
            duration_seconds=0.0,
            error_message=err_msg,
        )
        dummy_device = DeviceInfo(mode="UNKNOWN", vid=0, pid=0)
        logger.generate_github_summary(fail_res, dummy_device)
        if json_output:
            logger.export_json(json_output, fail_res, dummy_device)
        sys.exit(1)

    # Device selection / discovery logic
    target_device: DeviceInfo | None = None

    if mount:
        target_device = DeviceInfo(
            mode="BOOTSEL",
            vid=RASPBERRY_PI_VID,
            pid=RP2040_BOOTSEL_PID,
            mount_point=mount,
        )
        logger.log_info(f"Using specified mount point: {mount}")
    elif port:
        target_device = DeviceInfo(
            mode="RUNTIME",
            vid=SEEED_VID,
            pid=XIAO_RP2040_CDC_PID,
            port=port,
        )
        logger.log_info(f"Using specified serial port: {port}")
    else:
        logger.log_info("Scanning for connected XIAO-RP2040 devices...")
        discovered = device_mgr.find_devices()
        if not discovered:
            err_msg = "No XIAO-RP2040 devices found in RUNTIME or BOOTSEL mode."
            logger.log_error(err_msg)
            fail_res = FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=0.0,
                error_message=err_msg,
            )
            dummy_device = DeviceInfo(mode="UNKNOWN", vid=0, pid=0)
            logger.generate_github_summary(fail_res, dummy_device)
            if json_output:
                logger.export_json(json_output, fail_res, dummy_device)
            sys.exit(1)

        target_device = discovered[0]
        if len(discovered) > 1:
            logger.log_info(f"Multiple devices found. Selecting first device ({target_device.mode}).")

    # Reset if in RUNTIME mode
    if target_device.mode == "RUNTIME":
        logger.log_info(f"Device is in RUNTIME mode on {target_device.port}. Resetting to BOOTSEL mode...")
        try:
            target_device = device_mgr.reset_to_bootsel(target_device, timeout=timeout)
            logger.log_info(f"Device successfully reset to BOOTSEL mode at mount: {target_device.mount_point}")
        except Exception as e:  # noqa: BLE001
            err_msg = f"Failed to reset device to BOOTSEL mode: {e}"
            logger.log_error(err_msg)
            fail_res = FlashResult(
                success=False,
                bytes_written=0,
                duration_seconds=0.0,
                error_message=err_msg,
            )
            logger.generate_github_summary(fail_res, target_device)
            if json_output:
                logger.export_json(json_output, fail_res, target_device)
            sys.exit(1)

    # Flash firmware
    logger.log_info(f"Flashing firmware to BOOTSEL target (mount={target_device.mount_point})...")
    result = flasher.flash_uf2(
        str(firmware),
        target_device,
        use_picotool=use_picotool,
        verify=verify,
        verify_timeout=timeout,
    )

    if result.success:
        logger.log_info(
            f"Flash operation succeeded! {result.bytes_written} bytes written in {result.duration_seconds:.2f}s."
        )
    else:
        logger.log_error(f"Flash operation failed: {result.error_message}")

    logger.generate_github_summary(result, target_device)
    if json_output:
        logger.export_json(json_output, result, target_device)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
