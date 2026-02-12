#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

rm -rf "$ROOT_DIR/build/lambda"
mkdir -p "$ROOT_DIR/build/lambda"

uv pip install --target "$ROOT_DIR/build/lambda" "$ROOT_DIR"
mkdir -p "$ROOT_DIR/terraform/environments/dev/.tmp"
mkdir -p "$ROOT_DIR/terraform/environments/prod/.tmp"
