#!/usr/bin/env bash
set -euo pipefail

# Commit a known set of Laboratory changes one file at a time.
# Run from anywhere inside the repository. This script does not push.

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: not inside a Git repository." >&2
  exit 1
}
cd "$repo_root"

if ! git diff --cached --quiet; then
  echo "Error: the index already contains staged changes." >&2
  echo "Commit or unstage them before running this script." >&2
  exit 1
fi

files=(
  ".github/workflows/build-verification.yml"
  "address-before-operator.tex"
  "continuation-geometry/maintenance_convergence.tex"
  "continuation-geometry/synthesis-custodian-architecture.tex"
  "deployment_native_ternary_learning.tex"
  "inventory/README.md"
  "processing/distinction-and-continuation/chapters/ch01-latency-of-evidence.tex"
  "processing/distinction-and-continuation/chapters/ch02-accommodation-before-prediction.tex"
  "processing/distinction-and-continuation/chapters/ch03-theatre-of-agreement.tex"
  "processing/distinction-and-continuation/chapters/ch04-paracosm-trap.tex"
  "processing/distinction-and-continuation/chapters/ch10-clio-architecture.tex"
  "processing/distinction-and-continuation/chapters/ch11-constitutional-space-of-refusal.tex"
  "processing/distinction-and-continuation/chapters/ch12-verify-seams.tex"
  "processing/distinction-and-continuation/chapters/ch13-verification-inheritance.tex"
  "processing/distinction-and-continuation/chapters/ch14-model-capsules.tex"
  "processing/distinction-and-continuation/chapters/ch15-compression-fallacy.tex"
  "processing/distinction-and-continuation/chapters/ch16-compression-after-expansion.tex"
  "processing/distinction-and-continuation/chapters/ch17-sparse-holographic-steganography.tex"
  "processing/distinction-and-continuation/chapters/ch18-clifford-fhe.tex"
  "processing/distinction-and-continuation/chapters/ch19-ledgers-without-value.tex"
  "processing/distinction-and-continuation/chapters/ch20-rebel-without-a-cost.tex"
  "processing/distinction-and-continuation/chapters/ch21-unfinishable-games.tex"
  "processing/glass-meridian.tex"
  "source/operator-residue.tex"
  "source/representational-simplicity.tex"
)

messages=(
  "Fix headless rendering workflow"
  "Place citations in Address Before Operator"
  "Verify citations in Maintenance Convergence"
  "Place citations in Synthesis Custodian Architecture"
  "Place citations in Native Ternary Learning"
  "Document repository inventory"
  "Place citations in Latency of Evidence"
  "Place citations in Accommodation Before Prediction"
  "Place citations in Theatre of Agreement"
  "Place citations in The Paracosm Trap"
  "Place citations in CLIO Architecture"
  "Place citations in Constitutional Space of Refusal"
  "Place citations in Verify Seams"
  "Place citations in Verification Inheritance"
  "Place citations in Model Capsules"
  "Place citations in The Compression Fallacy"
  "Place citations in Compression After Expansion"
  "Place citations in Sparse Holographic Steganography"
  "Place citations in Clifford FHE"
  "Place citations in Ledgers Without Value"
  "Place citations in Rebel Without a Cost"
  "Place citations in Unfinishable Games"
  "Place citations in Glass Meridian"
  "Place citations in Operator Residue"
  "Verify citations in Representational Simplicity"
)

if ((${#files[@]} != ${#messages[@]})); then
  echo "Error: internal file/message count mismatch." >&2
  exit 1
fi

for file in "${files[@]}"; do
  if [[ ! -e "$file" ]]; then
    echo "Error: expected file is missing: $file" >&2
    exit 1
  fi
done

for i in "${!files[@]}"; do
  file=${files[$i]}
  message=${messages[$i]}

  if git diff --quiet -- "$file"; then
    echo "Skipping unchanged file: $file"
    continue
  fi

  git add -- "$file"

  if ! git diff --cached --check; then
    git restore --staged -- "$file"
    echo "Error: diff check failed for $file; nothing from it was committed." >&2
    exit 1
  fi

  git commit -m "$message" -- "$file"
done

echo
echo "Finished committing listed changes one file at a time."
echo "Review with: git status --short && git log --oneline -25"
echo "No push was performed."

