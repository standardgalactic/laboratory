#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output="${1:-$root/output}"
export PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}"

for script in "$root"/experiments/*.py; do
    blender -b --python-exit-code 1 -P "$script" -- --output "$output"
done

printf 'Sixteen experiment renders written to %s\n' "$output"
