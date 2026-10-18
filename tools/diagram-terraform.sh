#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
diagram_dir="$(mktemp -d "${TMPDIR:-/tmp}/point-l3-diagram.XXXXXX")"
trap 'rm -r "$diagram_dir"' EXIT

# Mount only a temporary copy of Terraform sources and a synthetic plan.
mkdir -p "$diagram_dir/terraform" "$project_dir/docs"
bash "$project_dir/tools/terraform-generate.sh" "$diagram_dir/terraform"
cp "$project_dir/tools/diagram-providers.tf.txt" "$diagram_dir/terraform/providers_override.tf"
cp "$diagram_dir/terraform/terraform.tfvars.example" "$diagram_dir/terraform/diagram.tfvars"

export TF_DATA_DIR="$diagram_dir/.terraform"
terraform -chdir="$diagram_dir/terraform" init -backend=false -input=false
terraform -chdir="$diagram_dir/terraform" plan -refresh=false -input=false -var-file=diagram.tfvars -out="$diagram_dir/plan"
terraform -chdir="$diagram_dir/terraform" show -json "$diagram_dir/plan" > "$diagram_dir/architecture.plan.json"
terraform -chdir="$diagram_dir/terraform" graph > "$diagram_dir/architecture.graph.dot"

# Keep IAM resources visible: --simplified would omit the L3 resources.
for format in png svg; do
  docker run --rm -v "$diagram_dir:/project" \
    patrickchugh/terravision@sha256:6bb96c63cc6f072014c58a665e5c4cc53dd0f29976b4f6e774edf5536915e786 \
    draw --source /project/terraform \
    --planfile /project/architecture.plan.json \
    --graphfile /project/architecture.graph.dot \
    --outfile /project/terraform-architecture --format "$format" \
    --title "Point Award - L3 Account"
done

cp "$diagram_dir"/terraform-architecture-aws.dot.* "$project_dir/docs/"
