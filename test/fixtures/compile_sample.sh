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

echo "Configuring arduino-cli for RP2040..."
"${ARDUINO_CLI}" config init --overwrite || true
"${ARDUINO_CLI}" config add board_manager.additional_urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json || true

retry_cmd() {
  local n=1
  local max=5
  local delay=5
  while true; do
    if "$@"; then
      return 0
    else
      if [ $n -ge $max ]; then
        echo "Command '$*' failed after $n attempts."
        return 1
      fi
      echo "Command '$*' failed (attempt $n/$max). Retrying in ${delay}s..."
      sleep $delay
      n=$((n+1))
      delay=$((delay * 2))
    fi
  done
}

echo "Updating arduino-cli index with retries..."
retry_cmd "${ARDUINO_CLI}" core update-index

echo "Installing RP2040 core with retries..."
retry_cmd "${ARDUINO_CLI}" core install rp2040:rp2040

echo "Compiling sample sketch for Seeed XIAO-RP2040..."
"${ARDUINO_CLI}" compile --fqbn rp2040:rp2040:seeed_xiao_rp2040 "${SKETCH_DIR}" --output-dir "${BUILD_DIR}"

echo "Compilation successful. Output binaries generated in ${BUILD_DIR}:"
ls -la "${BUILD_DIR}"
