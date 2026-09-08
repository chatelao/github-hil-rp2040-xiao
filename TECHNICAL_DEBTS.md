# Technical Debts: XIAO-RP2040 Firmware Flasher

This document logs technical debts identified during the design and implementation of the Seeed Studio XIAO-RP2040 firmware flasher CLI tool and GitHub Action integration. Per project guidelines, these technical debts are recorded here and will not be modified or refactored unless explicitly requested.

---

## Technical Debts Overview

| ID | Area | Description | Impact | Mitigation / Workaround |
| :--- | :--- | :--- | :--- | :--- |
| **TD-001** | Transport | External binary dependency on `picotool` for raw USB flashing fallback. | Subprocess execution fails if `picotool` is not installed or available in PATH. | Default to UF2 volume file copying; `picotool` is only invoked when `-u`/`--use-picotool` flag is explicitly set. |
| **TD-002** | Testing | Test suite relies on virtual serial pty simulation and mock mount fixtures rather than physical USB RP2040 silicon. | Real hardware USB controller quirks (e.g. OS-level USB re-enumeration delay variations) are simulated synthetic models. | Harness tests covers full 1200-baud reset state machine and mount lifecycle; real hardware integration testing performed on HIL runners. |
| **TD-003** | Telemetry | Serial data collection uses synchronous polling loop (`in_waiting` read) on main thread. | Blocks main CLI thread for requested duration (default 20s) without async callback or background daemon option. | Duration is configurable (`-d`/`--duration`); CLI displays clear progress updates while recording. |
| **TD-004** | Discovery | Drive mount detection relies on volume label matching (`RPI-RP2`) via `psutil`. | Systems with custom RP2040 bootloader builds using different volume labels will fail auto-discovery. | Allow explicit mount path specification via `-m`/`--mount` option. |

---

## Detailed Technical Debt Items

### TD-001: External Binary Dependency for `picotool` Fallback
- **Component**: `xiao_flasher.flasher.PicotoolTransport`
- **Description**: The fallback transport relies on invoking system subprocesses (`picotool load` and `picotool reboot`).
- **Rationale**: Direct USB raw access without mass storage mounting requires `picotool`. Avoids bundling native OS binaries within Python package distribution.
- **Future Resolution**: Embed optional native bindings or `pyusb` direct RP2040 bootrom vendor interface commands if standalone raw flashing without `picotool` binary is required.

### TD-002: Synthetic Hardware Simulation in Automated Test Suite
- **Component**: `test/test_hardware_harness.py`
- **Description**: Hardware integration tests use POSIX `pty` / `termios` virtual serial pairs and temporary directory disk mounts to simulate 1200-baud reset and BOOTSEL transitions.
- **Rationale**: Enables headless CI testing without physical USB hardware connected to GitHub Actions runners.
- **Future Resolution**: Extend HIL (Hardware-in-the-Loop) runner farm with physical XIAO-RP2040 USB hardware devices.

### TD-003: Synchronous Polling Loop for Serial Data Collection
- **Component**: `xiao_flasher.telemetry.TelemetryLogger.collect_serial_data`
- **Description**: Serial collection operates in a single-threaded blocking loop (`time.sleep(0.05)`) for the requested duration.
- **Rationale**: Simple, cross-platform implementation with low CPU footprint and predictable cleanup logic.
- **Future Resolution**: Implement an asynchronous thread-based or event-driven reader queue for background non-blocking serial collection.

### TD-004: Hardcoded BOOTSEL Volume Label Matching
- **Component**: `xiao_flasher.discovery.DeviceManager.find_bootsel_devices`
- **Description**: Disk partitions are identified as RP2040 BOOTSEL volumes by matching volume labels against `RPI-RP2`.
- **Rationale**: Standard factory RP2040 bootloader ROM volume label across Seeed Studio XIAO-RP2040 and Raspberry Pi Pico boards.
- **Future Resolution**: Allow user configuration of custom bootloader volume labels in config file or CLI flags.
