# Technical Debts

This document logs known technical debts and limitations identified during implementation. Per project guidelines, these items are tracked here and should not be modified or refactored unless explicitly requested.

## Identified Technical Debts

1. **Simulated Hardware Test Fixture Binary Requirement**
   - **Description**: In `test/test_hardware_harness.py`, integration tests for flashing actual compiled binaries require `arduino-cli` to compile `test/fixtures/sample_sketch/sample_sketch.ino` into `.uf2`. If `arduino-cli` or RP2040 core index is unavailable during offline testing, the integration test skips execution.
   - **Impact**: E2E test execution is skipped in offline or incomplete build environments.
   - **Potential Solution**: Provide pre-compiled lightweight fallback UF2 stub fixtures or pre-built mock UF2 binaries in `test/fixtures/`.

2. **Picotool Fallback Subprocess Dependency**
   - **Description**: Flashing via `picotool` option (`--use-picotool` / `-u`) relies on calling external binary `picotool` as a subprocess.
   - **Impact**: Requires users or runner environments to manually install `picotool` and libusb drivers if `--use-picotool` flag is explicitly set.
   - **Potential Solution**: Implement optional dynamic libusb detection or auto-download script for `picotool` binary dependencies in GitHub Action workflows.

3. **1200-Baud Baud Touch Port Detection Delays**
   - **Description**: Post-reset serial port re-enumeration polling waits up to `timeout` seconds (default 10s) using polling loops (`time.sleep(0.5)`).
   - **Impact**: Introduces slight fixed polling overhead when device CDC port re-appears faster than polling intervals.
   - **Potential Solution**: Use event-driven OS device notification hooks (e.g. `udev` on Linux or `WM_DEVICECHANGE` on Windows) for instant device re-enumeration detection.
