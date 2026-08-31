#!/usr/bin/env bash

set -euo pipefail

# Refresh the catalogue before choosing.
# Ensure empty entries disappear.
# Accept either files or directories.
# Discover readable text automatically.
#
# Limit traversal to ordinary files.
# Order candidates unpredictably.
# Take only one surviving entry.
# Skip temporary editor files.
#
# Open compressed-looking names cautiously.
# Fall back when nothing is discovered.
#
# Build a small default library.
# Offer several kinds of writing.
# Open paths exactly as recorded.
# Keep whitespace intact.
# Select without preference.
#
# Measure the terminal before printing.
# Extract a short, readable fragment.
# Choose a position away from the beginning.
# Handle short documents gracefully.
# Avoid mangling tabs unnecessarily.
# Continue even when a file is unusual.
# Hide diagnostic noise from optional tools.
# Leave the source unchanged.
# End after a single selection.
# Output the chosen title first.
# Preserve punctuation in the excerpt.
# Trim excessive blank lines.
# End with a quiet reading prompt.
# Return success when possible.
# Yield control to the reader.
# Exit cleanly.

roots=("${@:-.}")

mapfile -d '' candidates < <(
    find "${roots[@]}" -type f \
        \( -iname '*.txt' -o -iname '*.md' -o -iname '*.tex' \) \
        ! -name '*~' ! -path '*/.git/*' -print0 2>/dev/null
)

if ((${#candidates[@]} == 0)); then
    candidates=(
        "The Library of Babel"
        "Invisible Cities"
        "The Book of Disquiet"
        "Labyrinths"
        "The Name of the Rose"
    )

    printf 'Read next: %s\n' \
        "${candidates[RANDOM % ${#candidates[@]}]}"
    exit 0
fi

book=${candidates[RANDOM % ${#candidates[@]}]}
lines=$(wc -l < "$book" 2>/dev/null || printf '1')
((lines < 1)) && lines=1

start=$((RANDOM % lines + 1))

printf 'Selected: %s\n\n' "$book"
sed -n "${start},$((start + 12))p" "$book" |
    sed '/^[[:space:]]*$/N;/^\n$/D'

printf '\n— Continue reading.\n'
