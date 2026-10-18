#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
python3 "$project_dir/tools/diagram-drawio.py"
