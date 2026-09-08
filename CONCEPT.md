# Concept: XIAO-RP2040 Firmware Flashing via GitHub Actions

## Goal

Alle nötigen Skripte um auf einem XIAO-RP2040 Board eine Firmware aus einem GitHub Action Flow zu installieren.
*(All required scripts to install firmware on a Seeed Studio XIAO-RP2040 board directly from a GitHub Actions workflow.)*

---

## Business Cases

1. **Automated CI/CD Hardware Provisioning & Testing**
   Enables continuous integration and deployment pipelines by automatically flashing compiled firmware artifacts onto physical target hardware (XIAO-RP2040) attached to self-hosted GitHub Action runners or test-bench systems.

2. **Simplified Developer Workflows & Standardization**
   Eliminates manual, error-prone board flashing steps for developers and test engineers by standardizing flashing scripts across local environments and CI/CD automation pipelines.

3. **Traceable & Reproducible Firmware Deployment**
   Ensures that firmware built by GitHub Actions can be deterministically verified and installed with automated status reporting, logs, and traceability back to specific Git commits/releases.

---

## Use Cases

### UC-1: Automated Firmware Flashing & Serial Data Collection in GitHub Actions Pipeline
- **Actor**: GitHub Actions Runner (Self-Hosted / Connected Hardware Runner)
- **Trigger**: GitHub Workflow event (e.g., commit push, release tag, or manual `workflow_dispatch`).
- **Main Success Scenario**:
  1. GitHub Workflow compiles firmware or retrieves build artifact (`.uf2` / `.bin` / `.elf`).
  2. Workflow invokes the automated flashing tool script.
  3. Script detects attached XIAO-RP2040 board and verifies its current state (Runtime vs. BOOTSEL bootloader mode).
  4. Script puts/resets the XIAO-RP2040 into BOOTSEL mode if necessary.
  5. Firmware binary is written to the device.
  6. Script collects serial output from USB-serial port for 20 seconds after flashing.
  7. Script packages collected serial output into a `.zip` file artifact and reports it back to GitHub.

### UC-2: Local Developer Firmware Flashing
- **Actor**: Firmware Developer
- **Trigger**: Execution of local CLI script.
- **Main Success Scenario**:
  1. Developer runs the CLI flashing script specifying the local firmware file.
  2. Script scans USB/serial ports to locate attached XIAO-RP2040 target device.
  3. Script flashes the target device and returns terminal status output.

### UC-3: Device Recovery & Bootloader State Verification
- **Actor**: CI Test Runner / Engineer
- **Trigger**: Unresponsive board state or corrupted target application firmware.
- **Main Success Scenario**:
  1. Script detects that the board is unresponsive over serial runtime interface.
  2. Script attempts bootloader trigger (e.g. 1200-baud reset trick or USB BOOTSEL detection).
  3. Flashing tool restores target device using base firmware image or flags device state in report logs.

---

## High-Level Architecture & Business Interfaces

### Top-Level Functional Components

1. **Workflow Integration Orchestrator**
   The entry point interface responsible for receiving execution parameters (firmware path, target device identifier, flags) from GitHub Actions or CLI invocations and controlling the execution flow.

2. **Device Discovery & Bootloader Controller**
   Scans host system USB buses and serial communication ports to identify attached XIAO-RP2040 hardware, determines whether the device is in runtime mode or RP2040 BOOTSEL bootloader mode, and handles software/hardware state transitions.

3. **Firmware Flasher Module**
   Handles binary transmission and byte verification to program the XIAO-RP2040 flash memory.

4. **Status & Logging Telemetry Module**
   Collects result metrics, error messages, and execution traces, exposing them back to GitHub Action step summaries or stdout/stderr.

```
+-----------------------------------------------------------------------+
|                    Workflow Integration Orchestrator                   |
+-----------------------------------+-----------------------------------+
                                    |
                    +---------------+---------------+
                    | I-Device-Management           | I-Firmware-Transport
                    v                               v
+-----------------------------------+   +-------------------------------+
|   Device Discovery & Bootloader   |   |   Firmware Flasher Module     |
|             Controller            |   |                               |
+-----------------------------------+   +-------------------------------+
                                    |
                                    | I-Telemetry-Log
                                    v
+-----------------------------------------------------------------------+
|                   Status & Logging Telemetry Module                    |
+-----------------------------------------------------------------------+
```

### Business / Functional Interfaces

- **`I-Workflow-Trigger`**: External parameter interface exposing workflow options (firmware artifact path, target port/serial number, timeout, dry-run flags).
- **`I-Device-Management`**: Internal functional interface between orchestrator and device discovery to query attached boards, detect RP2040 USB IDs (`288a:0003` / RP2040 bootloader `2e8a:0003`), and trigger reboot commands.
- **`I-Firmware-Transport`**: Storage and transport interface that streams firmware bytes to target memory via UF2 mass storage volume copy or `picotool` protocol.
- **`I-Telemetry-Log`**: Reporting interface returning formatted logs, error codes, and step execution summaries for GitHub Actions UI and developer CLI.

---

## Major Conceptual Choices & Evaluated Alternatives

### Choice 1: Flashing Transport Mechanism
- **Selected Choice**: **Option 1.1 - Mass Storage UF2 Mount & Picotool Transport**
- **Alternative 1.1 (Selected)**: Dual transport using native USB Mass Storage UF2 file copying when mounted, alongside `picotool` CLI interface integration. UF2 copying requires no special debug hardware and is native to the RP2040 bootloader ROM.
- **Alternative 1.2**: SWD Hardware Debug Probe Flashing (via OpenOCD / pyOCD and external debug probe). Discarded because requiring hardware SWD probes attached to every test runner adds external hardware complexity and cost when USB native flashing suffices.
- **Alternative 1.3**: Custom Serial UART Bootloader Protocol. Discarded because RP2040 already features native ROM UF2 and USB CDC support, making custom serial bootloader maintenance redundant.

### Choice 2: Scripting Environment & Platform Execution Stack
- **Selected Choice**: **Option 2.1 - Cross-Platform Python-based CLI Module**
- **Alternative 2.1 (Selected)**: Python-based CLI executable wrapped into reusable GitHub Action steps. Python provides cross-platform support (Linux, macOS, Windows) and established USB/serial hardware libraries (`pyusb`, `pyserial`).
- **Alternative 2.2**: Linux Shell Scripting (Bash + OS utilities `mount`/`cp`). Discarded due to lack of native cross-platform support (e.g. Windows runners) and fragile platform-dependent disk mounting logic.
- **Alternative 2.3**: Containerized Docker Action Execution. Discarded because mapping raw USB devices and serial ports into Docker containers across various host operating systems introduces privilege issues and host driver restrictions.

### Choice 4: Post-Flash Serial Data Collection & Artifact Packaging
- **Selected Choice**: **Option 4.1 - 20-Second USB-Serial CDC Stream Capture to Zipped Archive**
- **Alternative 4.1 (Selected)**: Automated 20-second streaming data collection on the re-enumerated CDC USB serial port after flashing, packaged into a `.zip` file for GitHub Actions artifact uploading.
- **Alternative 4.2**: Infinite continuous logging without duration timeout. Discarded because CI/CD jobs require deterministic bounded execution timeouts.
- **Alternative 4.3**: Uncompressed raw text log artifact upload. Discarded because zip archiving reduces bandwidth and storage overhead in workflow runs.

### Choice 3: Bootloader Mode Triggering Strategy
- **Selected Choice**: **Option 3.1 - Hybrid Software Reset Trick (1200-baud touch) with Dynamic BOOTSEL Detection**
- **Alternative 3.1 (Selected)**: Automated reset into BOOTSEL mode via 1200-baud CDC touch (or `picotool reboot -f -u`) combined with automatic UF2 drive detection.
- **Alternative 3.2**: Manual BOOTSEL Hardware Button Requirement. Discarded because manual button presses prevent automated headless CI/CD workflow execution on remote runners.
- **Alternative 3.3**: Dedicated Hardware Relay/GPIO Pin Toggle for RUN/BOOTSEL. Discarded as primary choice due to extra wiring/hardware requirements, though noted as a fallback option for dedicated hardware test rigs.

---

## Summary of Discarded Alternatives

Below is the summary of discarded alternatives evaluated during conceptual design:

1. **SWD Hardware Debug Probe Flashing (OpenOCD/pyOCD)**: Discarded due to unnecessary hardware probe dependencies for basic firmware flashing.
2. **Custom Serial UART Bootloader**: Discarded due to unnecessary software overhead given native RP2040 ROM UF2 capability.
3. **Pure Bash / OS-Shell Flashing Scripts**: Discarded due to lack of cross-platform portability (especially Windows compatibility).
4. **Docker Container Flashing Environment**: Discarded due to OS-level USB device pass-through complexities in containerized environments.
5. **Strict Manual BOOTSEL Button Triggering**: Discarded due to incompatibility with unattended remote GitHub Action runners.
6. **Dedicated GPIO Hardware Reset Circuitry**: Discarded as a baseline requirement to keep hardware setup simple, preserved only as an edge-case test-bench extension.
7. **Unbounded Serial Logging**: Discarded in favor of 20-second timed data collection to ensure deterministic workflow step exit times.
8. **Uncompressed Raw Log Artifacts**: Discarded in favor of zipped archive reports (`.zip`).
