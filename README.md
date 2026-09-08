# XIAO-RP2040 Firmware Flasher

Automated firmware flashing tool and GitHub Action for Seeed Studio XIAO-RP2040 boards with USB serial data collection and zipped report creation.

## Architecture

![Top Architecture](https://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/chatelao/github-hil-rp2040-xiao/main/TOP_ARCHITECTURE.puml)

## Installation

Install runtime dependencies and the package:

```bash
./src/install.sh
```

To install test dependencies (`pytest`, `pytest-cov`, `mypy`, `ruff`):

```bash
./test/install.sh
```

## CLI Usage

Run `xiao-flash` with mandatory or optional flags:

```bash
# Flash firmware and collect USB-serial data for 20 seconds into a zip file
xiao-flash -f build/firmware.uf2 -c -d 20 -z serial_log.zip
```

### Options Reference

All CLI flags support both short and long forms:

| Short Flag | Long Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `-f` | `--firmware` | Path to `.uf2` firmware file | *Required* |
| `-p` | `--port` | Target CDC serial port (e.g. `/dev/ttyACM0` or `COM3`) | Auto-detect |
| `-m` | `--mount` | Target BOOTSEL volume mount point | Auto-detect |
| `-u` | `--use-picotool` | Use `picotool` fallback for raw USB flashing | False |
| `-v` / `-nv` | `--verify` / `--no-verify` | Enable or disable post-flash unmount verification | True |
| `-j` | `--json-output` | Path to export structured JSON execution summary | None |
| `-t` | `--timeout` | Timeout in seconds for device reset and verification | 10.0 |
| `-c` | `--collect-serial` | Collect serial output after flashing | False |
| `-d` | `--duration` | Duration in seconds to collect serial data | 20.0 |
| `-z` | `--zip-output` | Path to save compressed `.zip` file containing collected serial log | None |

## GitHub Action Usage

Integrate `xiao-flasher` into your GitHub Action workflows:

```yaml
- name: Flash XIAO-RP2040 Firmware and Collect Serial Artifacts
  uses: chatelao/github-hil-rp2040-xiao@main
  with:
    firmware: 'build/firmware.uf2'
    collect-serial: 'true'
    duration: '20'
    zip-output: 'serial_log.zip'
```
