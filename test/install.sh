#!/usr/bin/env bash
set -e

echo "Installing test dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pytest pytest-cov mypy ruff
echo "Test dependencies installation completed successfully."
