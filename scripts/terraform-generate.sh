#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
template_dir="$project_dir/scripts/terraform/templates"
output_dir="${1:-$project_dir/terraform}"

mkdir -p "$output_dir"

while IFS= read -r -d '' template; do
  relative_path="${template#"$template_dir"/}"
  destination="$output_dir/${relative_path%.tmpl}"
  mkdir -p "$(dirname "$destination")"
  cp "$template" "$destination"
done < <(find "$template_dir" -type f -name '*.tmpl' -print0 | sort -z)

printf 'Terraform files generated in %s\n' "$output_dir"
