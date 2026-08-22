#!/usr/bin/env bash
# build.sh — compile Distinction and Continuation
#
# Usage:
#   ./build.sh              # full manuscript (main.tex), two-pass
#   ./build.sh part3        # just Part III, two-pass
#
# Engine: XeLaTeX by default. If font-loading issues arise (as with
# LuaLaTeX's font cache in some environments), this is already the
# fallback engine per established convention — no change needed.

set -e

TARGET="${1:-main}"

if [ "$TARGET" = "main" ]; then
  xelatex -interaction=nonstopmode main.tex
  xelatex -interaction=nonstopmode main.tex
  echo "Built main.pdf"
else
  cd parts
  xelatex -interaction=nonstopmode "${TARGET}.tex"
  xelatex -interaction=nonstopmode "${TARGET}.tex"
  echo "Built parts/${TARGET}.pdf"
fi
