#!/usr/bin/env bash
set -e

echo "Installing xiao-flasher runtime dependencies and package..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .
echo "Runtime installation completed successfully."
