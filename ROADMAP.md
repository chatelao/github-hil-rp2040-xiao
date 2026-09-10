# Project Roadmap: XIAO-RP2040 Firmware Flashing via GitHub Actions

## Progress Overview

| Phase | Description | Status |
| :--- | :--- | :---: |
| **Phase 1** | Project Setup & CI/CD Infrastructure | ✅ |
| **Phase 2** | Technical Interfaces & Data Models Definition | ✅ |
| **Phase 3** | Core Module Implementation | ✅ |
| **Phase 4** | GitHub Action Packaging & Integration Testing | ✅ |
| **Phase 5** | Documentation & Release Finalization | ✅ |
| **Phase 6** | Maintenance & Advanced Telemetry Enhancements | ⏳ |

---

## Goals

- ✅ **Automated CI/CD Flashing**: Provide a GitHub Composite Action to automatically flash firmware onto Seeed Studio XIAO-RP2040 boards attached to runners.
- ✅ **Cross-Platform Developer CLI**: Deliver a cross-platform Python CLI tool (`xiao-flash`) supporting Linux, macOS, and Windows.
- ✅ **Dual Flashing Transport**: Support UF2 volume copying and `picotool` as a fallback mechanism.
- ✅ **Reliable State Transitions**: Implement automatic 1200-baud rate serial touch reset to switch from Runtime CDC mode to BOOTSEL mode.
- ✅ **Comprehensive Telemetry & Serial Collection**: Output structured CLI logging, JSON test reports, GitHub Actions step summaries, and collect USB-serial output for 20 seconds as a zipped archive artifact (`.zip`).
- ⏳ **Advanced Telemetry & Debt Mitigations**: Enhance serial data collection to support background non-blocking execution and configurable volume label detection.

---

## Phases

### Phase 1: Project Setup & CI/CD Infrastructure

- [x] **Task 1.1: Environment & Repository Structure Setup** (2026-09-07 08:02 UTC)
  - [x] Create Python project structure (`src/xiao_flasher/`, `test/`) with `pyproject.toml` / `setup.py`.
  - [x] Implement `src/install.sh` for runtime installation setup.
  - [x] Implement `test/install.sh` for installing test dependencies (`pytest`, `pytest-cov`, `mypy`, `ruff`).
- [x] **Task 1.2: CI/CD Pipeline Initial Setup** (2026-09-07 08:30 UTC)
  - [x] Create GitHub Actions workflow (`.github/workflows/ci.yml`) for linting, type-checking, and running unit tests on every commit/PR.
  - [x] Configure dependency and build caching in GitHub Actions workflows.

---

### Phase 2: Technical Interfaces & Data Models Definition

*Note: Interface definitions are established first to enable parallelized development of underlying modules.*

- [x] **Task 2.1: Data Models Definition (`xiao_flasher.models`)** (2026-09-07 11:54 UTC)
  - [x] Define `DeviceInfo` dataclass (port, mount point, mode, serial number, VID, PID).
  - [x] Define `FlashResult` dataclass (success, bytes written, duration, error message).
- [x] **Task 2.2: Device Management Interface (`xiao_flasher.discovery`)** (2026-09-07 11:54 UTC)
  - [x] Define `IDeviceManagement` abstract base class (`find_devices`, `reset_to_bootsel`).
- [x] **Task 2.3: Firmware Transport Interface (`xiao_flasher.flasher`)** (2026-09-07 11:54 UTC)
  - [x] Define `IFirmwareTransport` abstract base class (`validate_firmware`, `flash_uf2`).
- [x] **Task 2.4: Telemetry & Logging Interface (`xiao_flasher.telemetry`)** (2026-09-07 11:54 UTC)
  - [x] Define `ITelemetryLog` abstract base class (`log_info`, `log_error`, `generate_github_summary`).

---

### Phase 3: Core Module Implementation

- [x] **Task 3.1: Device Discovery & Bootloader Controller (`xiao_flasher.discovery`)** (2026-09-07 16:25 UTC)
  - [x] Implement USB CDC runtime port detection (VID:PID `288a:0003` / custom) using `pyserial`.
  - [x] Implement BOOTSEL volume detection (`RPI-RP2`, VID:PID `2e8a:0003`) using `psutil.disk_partitions()`.
  - [x] Implement 1200-baud touch reset logic to reboot device from runtime to BOOTSEL mode.
  - [x] Unit test discovery logic with mock serial and volume fixtures.
- [x] **Task 3.2: Firmware Flasher Module (`xiao_flasher.flasher`)** (2026-09-07 18:00 UTC)
  - [x] Implement UF2 header validation (family ID `0xe48dba66` for RP2040).
  - [x] Implement UF2 binary file streaming to mounted `RPI-RP2` volume.
  - [x] Implement `picotool` execution fallback for raw USB programming.
  - [x] Implement post-flash verification (volume unmount detection and CDC serial re-enumeration polling).
  - [x] Unit test flasher module with file system mocks.
- [x] **Task 3.3: Telemetry & Logging Module (`xiao_flasher.telemetry`)** (2026-09-07 19:15 UTC)
  - [x] Implement console logger with ANSI color formatting.
  - [x] Implement GitHub Actions Step Summary reporter (`$GITHUB_STEP_SUMMARY`).
  - [x] Implement structured JSON result exporter (`--json-output`).
  - [x] Implement 20-second USB serial data collection and `.zip` archive creation (`collect_serial_data`).
  - [x] Unit test telemetry report generation and serial log zipping.
- [x] **Task 3.4: CLI & Workflow Integration Orchestrator (`xiao_flasher.cli`)** (2026-09-07 20:30 UTC)
  - [x] Implement CLI argument parsing using `Click` (support short `-f` and long `--firmware` options for all CLI flags).
  - [x] Integrate orchestrator flow calling discovery, flasher, and telemetry modules.
  - [x] Unit test CLI entry point and exit code handling.

---

### Phase 4: GitHub Action Packaging & Integration Testing

- [x] **Task 4.1: Composite GitHub Action (`action.yml`)** (2026-09-07 21:15 UTC)
  - [x] Create `action.yml` defining action inputs (firmware path, target port, timeout, forced mode, serial collection options).
  - [x] Add Python environment setup, `xiao-flasher` execution, and serial `.zip` log artifact upload step.
- [x] **Task 4.2: Simulated Hardware Test Harness** (2026-09-07 22:00 UTC)
  - [x] Implement virtual serial port device simulator for 1200-baud touch reset handling.
  - [x] Implement mock BOOTSEL volume state transition fixture and post-flash verification harness.
  - [x] Add unit and end-to-end integration tests using the simulated hardware harness in `test/test_hardware_harness.py`.
- [x] **Task 4.3: Target Sample Firmware Compilation Setup** (2026-09-08 05:20 UTC)
  - [x] Add target RP2040 sample sketch source files in `test/fixtures/sample_sketch/`.
  - [x] Add automated compilation script using `arduino-cli` with RP2040 core index to produce target `.uf2` binaries.
- [x] **Task 4.4: End-to-End CI Workflow Integration** (2026-09-08 06:00 UTC)
  - [x] Update `.github/workflows/ci.yml` to include end-to-end simulated hardware flashing verification and action step execution.

---

### Phase 5: Documentation & Polish

- [x] **Task 5.1: Project Documentation** (2026-09-08 07:15 UTC)
  - [x] Update `README.md` with usage instructions, CLI options reference, and GitHub Action integration examples.
  - [x] Ensure all technical debts identified during implementation are logged in `TECHNICAL_DEBTS.md`.
- [x] **Task 5.2: Final Release Preparation** (2026-09-08 08:00 UTC)
  - [x] Validate codebase against `CONCEPT.md`, `DESIGN.md`, and `GEMINI.md` requirements.
  - [x] Perform pre-commit validation and freeze release v1.0.0 tag.

---

### Phase 6: Maintenance & Advanced Telemetry Enhancements

*Note: Interface definitions are established first to enable parallelized development of underlying modules.*

- [ ] **Task 6.1: Async Serial Reader Interface Definition (`xiao_flasher.telemetry`)**
  - [ ] Define `IAsyncSerialReader` interface for non-blocking background USB serial data capture (`TD-003`).
  - [ ] Add unit tests for asynchronous serial logging interface contract.
- [ ] **Task 6.2: Custom Volume Label Support Interface (`xiao_flasher.discovery`)**
  - [ ] Extend `IDeviceManagement` interface and CLI options (`-l`/`--label`) to accept custom BOOTSEL volume labels (`TD-004`).
  - [ ] Add unit tests for custom volume label matching logic.
- [ ] **Task 6.3: Async Telemetry Implementation & CLI Integration**
  - [ ] Implement thread-based background worker in `TelemetryLogger` for async serial collection without blocking main thread.
  - [ ] Update CLI options and action inputs to support asynchronous background collection mode.
