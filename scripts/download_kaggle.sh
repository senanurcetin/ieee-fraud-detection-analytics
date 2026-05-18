#!/usr/bin/env bash
set -euo pipefail

RAW_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/raw/kaggle_ieee_fraud"
mkdir -p "$RAW_DIR"

kaggle competitions download -c ieee-fraud-detection -p "$RAW_DIR"
unzip -o "$RAW_DIR/ieee-fraud-detection.zip" -d "$RAW_DIR"
