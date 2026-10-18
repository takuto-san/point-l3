#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
diagram_dir="$(mktemp -d "${TMPDIR:-/tmp}/point-drawio.XXXXXX")"
trap 'rm -r "$diagram_dir"' EXIT

# Mount only the diagram definition and generator, not Terraform state or credentials.
mkdir -p "$diagram_dir/docs" "$diagram_dir/tools"
cp "$project_dir/docs/architecture.tvg.json" "$diagram_dir/docs/"
cp "$project_dir/tools/diagram-drawio.py" "$diagram_dir/tools/"

docker run --rm --user "$(id -u):$(id -g)" \
  -v "$diagram_dir:/work" -w /work python:3.12-alpine \
  python tools/diagram-drawio.py

cp "$diagram_dir/docs/architecture-aws.drawio" "$project_dir/docs/"
