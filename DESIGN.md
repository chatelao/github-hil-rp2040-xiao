# Detailed Design: XIAO-RP2040 Firmware Flashing via GitHub Actions

## Overview & Relationship to `CONCEPT.md`

This document details the software design and technical architecture for the Seeed Studio XIAO-RP2040 automated firmware flashing tool. It derives directly from `CONCEPT.md`, translating high-level functional requirements and business interfaces into concrete implementation choices, technical APIs, data structures, and deployment specifications for GitHub Actions and developer CLI environments.

---

## Top Architecture Diagram

The high-level system components and data flows are modeled in `TOP_ARCHITECTURE.puml`:

![Top Architecture](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/owner/repo/main/TOP_ARCHITECTURE.puml)

```
+-----------------------------------------------------------------------+
|                    Workflow Integration Orchestrator                   |
|                          (xiao_flasher.cli)                           |
+-----------------------------------+-----------------------------------+
                                    |
                    +---------------+---------------+
                    | I-Device-Management           | I-Firmware-Transport
                    v                               v
+-----------------------------------+   +-------------------------------+
|   Device Discovery & Bootloader   |   |   Firmware Flasher Module     |
|             Controller            |   |    (xiao_flasher.flasher)    |
|     (xiao_flasher.discovery)      |   |                               |
+-----------------------------------+   +-------------------------------+
                                    |
                                    | I-Telemetry-Log
                                    v
+-----------------------------------------------------------------------+
|                   Status & Logging Telemetry Module                    |
|                       (xiao_flasher.telemetry)                        |
+-----------------------------------------------------------------------+
```

---

## Detailed Architecture & Component Specifications

### 1. Workflow Integration Orchestrator (`xiao_flasher.cli`)
- **Responsibility**: Serves as the CLI entry point (`xiao-flash`) and GitHub Action execution harness. Parses command-line flags, validates input binary paths, configures execution parameters, coordinates execution across modules, and returns standard exit codes (`0` for success, non-zero for errors).
- **Sub-modules**:
  - `cli.py`: Options parsing and execution pipeline runner.
  - `config.py`: Configuration models (e.g. timeouts, device path overrides, forced mode options).

### 2. Device Discovery & Bootloader Controller (`xiao_flasher.discovery`)
- **Responsibility**: Detects connected Seeed Studio XIAO-RP2040 hardware across operating systems. Identifies device states:
  - **Runtime Mode**: USB CDC Serial Port (Default VID:PID `288a:0003` or custom user VID:PID).
  - **BOOTSEL Mode**: RP2040 Bootloader ROM USB Mass Storage drive (VID:PID `2e8a:0003`, Volume Label `RPI-RP2`).
- **State Transition Control**:
  - Performs 1200-baud rate baud-touch on runtime CDC serial ports to trigger software reboot into BOOTSEL bootloader mode.
  - Polls system mount tables until the `RPI-RP2` block device/volume becomes accessible.

### 3. Firmware Flasher Module (`xiao_flasher.flasher`)
- **Responsibility**: Manages the binary transfer to the RP2040 device.
- **Flashing Operations**:
  - **UF2 Copy**: Verifies UF2 family ID (`0xe48dba66` for RP2040) and streams `.uf2` binary directly into the mounted `RPI-RP2` volume root directory.
  - **Picotool Fallback**: Invokes `picotool load` / `picotool reboot` if USB raw access is requested or mass storage volume auto-mounting is disabled.
  - **Post-Flash Verification**: Monitors volume unmounting (indicating RP2040 flash completion and reset) and waits for optional CDC serial re-enumeration.

### 4. Status & Logging Telemetry Module (`xiao_flasher.telemetry`)
- **Responsibility**: Formats execution traces, errors, and timing metrics.
- **Outputs**:
  - Structured console output (using ANSI colors and status indicators).
  - GitHub Actions Step Summary (`$GITHUB_STEP_SUMMARY` Markdown report).
  - JSON summary reports for test automation frameworks (`--json-output <path>`).

---

## Technical Interfaces & Data Models

### Interfaces

#### `I-Device-Management`
```python
class DeviceInfo:
    port: str | None              # e.g. "/dev/ttyACM0" or "COM3"
    mount_point: str | None       # e.g. "/media/runner/RPI-RP2" or "E:\"
    mode: str                     # "RUNTIME", "BOOTSEL", or "UNKNOWN"
    serial_number: str | None
    vid: int
    pid: int

class IDeviceManagement:
    def find_devices() -> list[DeviceInfo]: ...
    def reset_to_bootsel(device: DeviceInfo, timeout: float = 10.0) -> DeviceInfo: ...
```

#### `I-Firmware-Transport`
```python
class FlashResult:
    success: bool
    bytes_written: int
    duration_seconds: float
    error_message: str | None

class IFirmwareTransport:
    def validate_firmware(file_path: str) -> bool: ...
    def flash_uf2(file_path: str, target_device: DeviceInfo) -> FlashResult: ...
```

#### `I-Telemetry-Log`
```python
class ITelemetryLog:
    def log_info(message: str) -> None: ...
    def log_error(message: str, error: Exception | None = None) -> None: ...
    def generate_github_summary(result: FlashResult, device: DeviceInfo) -> None: ...
```

---

## Tech Stack & Dependencies

- **Language**: Python 3.10+
- **CLI Framework**: `Click` (or `Typer`) for argument parsing and CLI flags.
- **Hardware Integration**:
  - `pyserial`: Serial communication and 1200-baud reset touch.
  - `pyusb` / `libusb`: Low-level USB device enumeration.
  - `psutil`: Cross-platform disk mount point detection (`RPI-RP2`).
- **Testing & Packaging**:
  - `pytest`: Unit and mock integration testing.
  - `setuptools` / `wheel`: Standard packaging.
  - GitHub Actions Composite Action (`action.yml`).

---

## Major Implementation Choices & Evaluated Alternatives

### Choice 1: Tech Stack & Implementation Language
- **Selected Choice**: **Option 1.1 - Python 3.10+ with `Click`, `pyserial`, and `psutil`**
- **Alternative 1.1 (Selected)**: Python 3.10+ implementation packaged as a standard PyPI package and executable. Python is natively available across Linux, macOS, and Windows GitHub Action runners, and has well-maintained hardware libraries (`pyserial`, `psutil`).
- **Alternative 1.2**: Node.js / TypeScript CLI with `@serialport/bindings-cpp` and native USB packages. Discarded due to C++ compilation dependencies during `npm install` on diverse runner operating systems.
- **Alternative 1.3**: Rust CLI binary compiled for multiple host targets. Discarded due to increased CI build pipeline complexity requiring cross-compilation matrices for runner platforms.

### Choice 2: Mass Storage Drive Detection Strategy
- **Selected Choice**: **Option 2.1 - Platform-Agnostic `psutil` Volume & USB ID Scanning**
- **Alternative 2.1 (Selected)**: Cross-platform disk partition scanning via `psutil.disk_partitions()` filtered by volume label `RPI-RP2`, combined with USB device VID:PID scanning (`2e8a:0003`). Provides instant detection without spawning OS-specific subprocesses.
- **Alternative 2.2**: Invoking native OS shell utilities (`lsblk` on Linux, `wmic`/`Get-Volume` on Windows, `diskutil` on macOS). Discarded due to OS shell parsing fragility and execution overhead.
- **Alternative 2.3**: Exclusive reliance on `picotool` command-line utility. Discarded because `picotool` requires installing custom `libusb` drivers/rules on all runner hosts, whereas file copy to mounted UF2 storage requires no extra driver installation.

### Choice 3: GitHub Action Packaging Strategy
- **Selected Choice**: **Option 3.1 - GitHub Composite Action (`action.yml`)**
- **Alternative 3.1 (Selected)**: Composite GitHub Action that sets up Python (if needed), installs `xiao-flasher`, and executes the command directly on the host runner. Works seamlessly on both hosted and self-hosted runners.
- **Alternative 3.2**: Docker Container GitHub Action (`Dockerfile`). Discarded because Docker container actions only run on Linux runners and complicate direct pass-through access to host USB serial ports and mounted drives.
- **Alternative 3.3**: Pre-compiled standalone single-file binary (e.g. PyInstaller executable). Discarded due to binary maintenance overhead across OS architectures.

### Choice 4: Post-Flash Verification & Re-enumeration Strategy
- **Selected Choice**: **Option 4.1 - UF2 Unmount Detection & Serial Re-enumeration Check**
- **Alternative 4.1 (Selected)**: Dual verification: monitoring volume unmount (RP2040 automatically unmounts upon successful UF2 write) followed by polling for CDC serial port re-appearance within a specified timeout.
- **Alternative 4.2**: Hardware SWD memory readback via OpenOCD probe. Discarded due to requirement for external debug hardware on runners.
- **Alternative 4.3**: Fire-and-forget (blind file copy without post-write verification). Discarded as unreliable for automated test pipelines.

---

## Summary of Discarded Alternatives

Below is the summary of discarded implementation alternatives:

1. **Node.js / TypeScript implementation**: Discarded due to native C++ binding compilation issues on host runners.
2. **Rust implementation**: Discarded due to build matrix complexity for cross-platform GitHub Action distribution.
3. **OS-specific shell utility invocation for drive mounts**: Discarded due to platform-dependent parsing fragility across Windows, macOS, and Linux.
4. **Mandatory `picotool` dependency**: Discarded due to driver setup prerequisites on headless host runners compared to native UF2 file copying.
5. **Docker Container GitHub Action packaging**: Discarded due to Linux-only restriction and USB/mount device pass-through limitations in containers.
6. **PyInstaller single-binary distribution**: Discarded due to platform binary maintenance overhead.
7. **SWD Hardware Memory Readback Verification**: Discarded due to external hardware probe dependencies.
8. **Fire-and-forget flashing without verification**: Discarded due to lack of error reporting and verification needed for reliable CI/CD pipelines.
