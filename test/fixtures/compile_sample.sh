#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKETCH_DIR="${SCRIPT_DIR}/sample_sketch"
BUILD_DIR="${SKETCH_DIR}/build"
BIN_DIR="${SCRIPT_DIR}/bin"

mkdir -p "${BIN_DIR}" "${BUILD_DIR}"

if ! command -v arduino-cli &> /dev/null; then
  if [ ! -f "${BIN_DIR}/arduino-cli" ]; then
    echo "Downloading arduino-cli..."
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="${BIN_DIR}" sh
  fi
  ARDUINO_CLI="${BIN_DIR}/arduino-cli"
else
  ARDUINO_CLI="arduino-cli"
fi

retry() {
  local retries=3
  local count=0
  until "$@"; do
    exit_code=$?
    count=$((count + 1))
    if [ $count -lt $retries ]; then
      echo "Command failed (exit code $exit_code). Retrying in 5 seconds... ($count/$retries)"
      sleep 5
    else
      echo "Command failed after $retries attempts."
      return $exit_code
    fi
  done
}

echo "Configuring arduino-cli for RP2040..."
"${ARDUINO_CLI}" config init --overwrite || true
"${ARDUINO_CLI}" config add board_manager.additional_urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json || true
retry "${ARDUINO_CLI}" core update-index
retry "${ARDUINO_CLI}" core install rp2040:rp2040

echo "Compiling sample sketch for Seeed XIAO-RP2040..."
"${ARDUINO_CLI}" compile --fqbn rp2040:rp2040:seeed_xiao_rp2040 "${SKETCH_DIR}" --output-dir "${BUILD_DIR}"

echo "Compilation successful. Output binaries generated in ${BUILD_DIR}:"
ls -la "${BUILD_DIR}"
