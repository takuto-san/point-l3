#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
diagram_dir="$(mktemp -d "${TMPDIR:-/tmp}/point-common-architecture.XXXXXX")"
trap 'rm -r "$diagram_dir"' EXIT

# Share a design graph, not credentials, source code, state, or a cloud account.
cp "$project_dir/docs/architecture.tvg.json" "$diagram_dir/architecture.tvg.json"
cp "$project_dir/docs/terravision.yml" "$diagram_dir/terravision.yml"
cp "$project_dir/tools/terravision.Dockerfile" "$diagram_dir/Dockerfile"
cp "$project_dir/tools/terravision-services.pth" "$diagram_dir/terravision-services.pth"
docker build -t point-terravision:0.55.0-ja "$diagram_dir"

for format in png svg; do
  docker run --rm -v "$diagram_dir:/project" point-terravision:0.55.0-ja \
    draw --source /project/architecture.tvg.json \
    --annotate /project/terravision.yml \
    --outfile /project/architecture-aws --format "$format"
done

cp "$diagram_dir"/architecture-aws.dot.* "$project_dir/docs/"
