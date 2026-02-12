#!/usr/bin/env bash
set -euo pipefail

export AWS_PROFILE=globode-dev
aws sso login

uv run pytest --cov=payme --cov-report=term-missing
