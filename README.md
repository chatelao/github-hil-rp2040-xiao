# XIAO-RP2040 Firmware Flasher

Automated firmware flashing tool and GitHub Action for Seeed Studio XIAO-RP2040 boards with USB serial data collection and zipped report creation.

## Architecture

![Top Architecture](https://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/chatelao/github-hil-rp2040-xiao/main/TOP_ARCHITECTURE.puml)

## CLI Usage

Install the package:

```bash
./src/install.sh
```

Flash firmware and collect serial logs for 20 seconds:

```bash
xiao-flash -f build/firmware.uf2 -c -d 20 -z serial_log.zip
```

### Options

- `-f, --firmware`: Path to `.uf2` firmware file.
- `-p, --port`: Target CDC serial port (e.g. `/dev/ttyACM0` or `COM3`).
- `-m, --mount`: Target BOOTSEL volume mount point.
- `-u, --use-picotool`: Use `picotool` fallback for raw USB flashing.
- `-v/-nv, --verify/--no-verify`: Enable or disable post-flash unmount verification.
- `-j, --json-output`: Path to export structured JSON execution summary.
- `-t, --timeout`: Timeout in seconds for device reset and verification.
- `-c, --collect-serial`: Collect serial output after flashing.
- `-d, --duration`: Duration in seconds to collect serial data (default: 20s).
- `-z, --zip-output`: Path to save compressed `.zip` file containing collected serial log.

## GitHub Action Usage

```yaml
- uses: owner/repo@main
  with:
    firmware: 'build/firmware.uf2'
    collect-serial: 'true'
    duration: '20'
    zip-output: 'serial_log.zip'
```
