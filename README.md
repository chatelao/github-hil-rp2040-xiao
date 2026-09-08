# XIAO-RP2040 Firmware Flasher

Automated firmware flashing tool and GitHub Composite Action for Seeed Studio XIAO-RP2040 microcontrollers with automatic 1200-baud rate reset, dual flashing transport support, post-flash CDC serial re-enumeration verification, and zipped serial telemetry log archiving.

---

## Architecture Overview

The system architecture and hardware state transitions are defined in [`TOP_ARCHITECTURE.puml`](TOP_ARCHITECTURE.puml):

![Top Architecture](https://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/chatelao/github-hil-rp2040-xiao/main/TOP_ARCHITECTURE.puml)

For detailed conceptual design and technological choices, refer to [`CONCEPT.md`](CONCEPT.md) and [`DESIGN.md`](DESIGN.md).

---

## Features

- **Automated Device State Transition**: Performs 1200-baud touch reset on CDC serial runtime ports (VID:PID `288a:0003`) to switch devices into BOOTSEL bootloader mode.
- **Dual Flashing Transport**:
  - Direct `.uf2` file streaming to mounted `RPI-RP2` volumes (RP2040 UF2 family ID `0xe48dba66`).
  - Fallback execution using `picotool` for raw USB programming.
- **Post-Flash Verification**: Monitors BOOTSEL volume unmounting and polls CDC serial port re-enumeration.
- **Telemetry & Logging**:
  - ANSI colored terminal output.
  - GitHub Actions Step Summary (`$GITHUB_STEP_SUMMARY`) generation.
  - Exportable structured JSON test execution reports.
  - Post-flash USB serial output capture for a configurable duration (default 20s), archived into a `.zip` artifact.

---

## Installation

Run the provided runtime installation script:

```bash
./src/install.sh
```

Or install locally using `pip`:

```bash
pip install -e .
```

---

## Command-Line Interface (CLI) Usage

The CLI command `xiao-flash` provides full control over discovery, flashing, and serial collection. Every CLI option is available in both short and long form formats.

### CLI Options Reference

| Short Option | Long Option | Description | Default |
| :--- | :--- | :--- | :--- |
| `-f` | `--firmware` | Path to target `.uf2` firmware file *(Required)*. | — |
| `-p` | `--port` | Target CDC serial port (e.g. `/dev/ttyACM0` or `COM3`). | Auto-detected |
| `-m` | `--mount` | Target BOOTSEL volume mount point (e.g. `/media/RPI-RP2` or `E:\`). | Auto-detected |
| `-u` | `--use-picotool` | Use `picotool` fallback for raw USB programming instead of UF2 copy. | `False` |
| `-v` / `-nv` | `--verify` / `--no-verify` | Enable or disable post-flash unmount & serial re-enumeration verification. | `True` |
| `-j` | `--json-output` | Path to export structured JSON execution summary. | None |
| `-t` | `--timeout` | Timeout in seconds for device reset, flashing, and verification. | `10.0` |
| `-c` | `--collect-serial` | Enable post-flash serial output collection. | `False` |
| `-d` | `--duration` | Duration in seconds to record serial data. | `20.0` |
| `-z` | `--zip-output` | Output zip file path to store collected serial log file. | `serial_log.zip` |

---

## CLI Examples

### 1. Standard UF2 Flashing & 20s Serial Log Capture

```bash
xiao-flash -f build/firmware.uf2 -c -d 20 -z serial_log.zip
```

### 2. Flash with Explicit Serial Port and Custom JSON Report Output

```bash
xiao-flash -f build/firmware.uf2 -p /dev/ttyACM0 -j build/flash_report.json
```

### 3. Flash using `picotool` Fallback Transport

```bash
xiao-flash -f build/firmware.uf2 -u -t 15.0
```

---

## GitHub Action Usage

Use the composite GitHub Action [`action.yml`](action.yml) in your workflows for hardware-in-the-loop (HIL) testing:

```yaml
name: RP2040 Firmware Flashing & Telemetry

on:
  push:
    branches: [ main ]

jobs:
  flash_and_test:
    runs-on: [ self-hosted, linux, xiao-rp2040 ]
    steps:
      - uses: actions/checkout@v4

      - name: Flash XIAO-RP2040 & Collect Serial Logs
        uses: ./
        with:
          firmware: 'build/firmware.uf2'
          collect-serial: 'true'
          duration: '20'
          zip-output: 'serial_log.zip'
          json-output: 'flash_summary.json'

      - name: Upload Serial Log Artifact
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: serial-log-archive
          path: serial_log.zip
```

---

## Development & Testing

Install development and testing dependencies:

```bash
./test/install.sh
```

Run test suite, code linting, and type checking:

```bash
ruff check .
mypy src test
pytest --cov=src/xiao_flasher
```

---

## Documentation Index

- [`CONCEPT.md`](CONCEPT.md) – High-level product vision, business use cases, and functional architecture.
- [`DESIGN.md`](DESIGN.md) – Detailed technological choices, sub-module specifications, and evaluated design alternatives.
- [`ROADMAP.md`](ROADMAP.md) – Project implementation phases and milestone progress tracking.
- [`TECHNICAL_DEBTS.md`](TECHNICAL_DEBTS.md) – Technical debt log and maintenance considerations.
