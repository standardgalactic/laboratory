#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$(pwd)"
CONFIG="$ROOT/config/default.conf"

load_config(){ source "$CONFIG"; }

stage_exists(){ [[ -f "$PROJECT/$1" ]]; }

run_prompt(){
 stage="$1"
 prompt="$ROOT/prompts/$stage.md"
 out="$2"
 echo "[zebra] $stage -> $out"
 {
   cat "$prompt"
   echo
   echo "# PROJECT"
   for f in "$PROJECT"/*.md; do
     [[ -f "$f" ]] && { echo; echo "## $(basename "$f")"; cat "$f"; }
   done
 } | "$MODEL_RUNNER" run "$GENERATOR_MODEL" > "$out"
}
