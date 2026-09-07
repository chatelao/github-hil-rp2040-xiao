# Project Roadmap: XIAO-RP2040 Firmware Flashing via GitHub Actions

## Progress Overview

| Phase | Description | Status |
| :--- | :--- | :---: |
| **Phase 1** | Project Setup & CI/CD Infrastructure | ✅ |
| **Phase 2** | Technical Interfaces & Data Models Definition | ✅ |
| **Phase 3** | Core Module Implementation | 🚧 |
| **Phase 4** | GitHub Action Packaging & Integration Testing | ⏳ |
| **Phase 5** | Documentation & Release Finalization | ⏳ |

---

## Goals

- ⏳ **Automated CI/CD Flashing**: Provide a GitHub Composite Action to automatically flash firmware onto Seeed Studio XIAO-RP2040 boards attached to runners.
- ⏳ **Cross-Platform Developer CLI**: Deliver a cross-platform Python CLI tool (`xiao-flash`) supporting Linux, macOS, and Windows.
- ⏳ **Dual Flashing Transport**: Support UF2 volume copying and `picotool` as a fallback mechanism.
- ⏳ **Reliable State Transitions**: Implement automatic 1200-baud rate serial touch reset to switch from Runtime CDC mode to BOOTSEL mode.
- ⏳ **Comprehensive Telemetry**: Output structured CLI logging, JSON test reports, and GitHub Actions step summaries.

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
- [ ] **Task 3.3: Telemetry & Logging Module (`xiao_flasher.telemetry`)**
  - [ ] Implement console logger with ANSI color formatting.
  - [ ] Implement GitHub Actions Step Summary reporter (`$GITHUB_STEP_SUMMARY`).
  - [ ] Implement structured JSON result exporter (`--json-output`).
  - [ ] Unit test telemetry report generation.
- [ ] **Task 3.4: CLI & Workflow Integration Orchestrator (`xiao_flasher.cli`)**
  - [ ] Implement CLI argument parsing using `Click` (support short `-f` and long `--firmware` options for all CLI flags).
  - [ ] Integrate orchestrator flow calling discovery, flasher, and telemetry modules.
  - [ ] Unit test CLI entry point and exit code handling.

---

### Phase 4: GitHub Action Packaging & Integration Testing

- [ ] **Task 4.1: Composite GitHub Action (`action.yml`)**
  - [ ] Create `action.yml` defining action inputs (firmware path, target port, timeout, forced mode).
  - [ ] Add Python environment setup and `xiao-flasher` package execution steps.
- [ ] **Task 4.2: End-to-End Integration Tests & Target Sample Compilation**
  - [ ] Develop simulated hardware test harness using virtual serial ports / loopback devices.
  - [ ] Set up automated compilation of an Arduino example sketch (e.g., Blink/Serial example) for Seeed Studio XIAO-RP2040 target platform using `arduino-cli`.
  - [ ] Integrate End-to-End test suite executing firmware compilation and flashing verification in GitHub Actions workflow.

---

### Phase 5: Documentation & Polish

- [ ] **Task 5.1: Project Documentation**
  - [ ] Update `README.md` with usage instructions, CLI options reference, and GitHub Action integration examples.
  - [ ] Ensure all technical debts identified during implementation are logged in `TECHNICAL_DEBTS.md`.
- [ ] **Task 5.2: Final Release Preparation**
  - [ ] Validate codebase against `CONCEPT.md`, `DESIGN.md`, and `GEMINI.md` requirements.
  - [ ] Perform pre-commit validation and freeze release v1.0.0 tag.
