#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$ROOT/bin/workbench" "$ROOT/install.sh" "$ROOT/lib/"*.sh

echo "Writing Workbench is ready."
echo
echo "Run:"
echo "  $ROOT/bin/workbench"
echo
echo "Optional shell alias:"
echo "  alias workbench='$ROOT/bin/workbench'"
