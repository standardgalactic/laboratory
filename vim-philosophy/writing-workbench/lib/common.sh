#!/usr/bin/env bash

set -o pipefail

WORKBENCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$WORKBENCH_ROOT/config/workbench.conf"

load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "Missing configuration: $CONFIG_FILE" >&2
        exit 1
    fi
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"

    PROJECTS_DIR="$WORKBENCH_ROOT/$PROJECTS_DIR"
    EXPORTS_DIR="$WORKBENCH_ROOT/$EXPORTS_DIR"
    LOGS_DIR="$WORKBENCH_ROOT/$LOGS_DIR"
    THEORY_DIR="$WORKBENCH_ROOT/$THEORY_DIR"
    PROMPTS_DIR="$WORKBENCH_ROOT/$PROMPTS_DIR"
}

die() {
    echo "Error: $*" >&2
    exit 1
}

pause() {
    printf "\nPress Enter to continue..."
    read -r _
}

slugify() {
    printf '%s' "$1" |
        tr '[:upper:]' '[:lower:]' |
        sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

project_path() {
    printf '%s/%s' "$PROJECTS_DIR" "$1"
}

list_projects() {
    find "$PROJECTS_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort
}

choose_project() {
    local projects selection
    mapfile -t projects < <(list_projects)
    ((${#projects[@]})) || die "No projects exist yet."

    if command -v fzf >/dev/null 2>&1; then
        selection="$(printf '%s\n' "${projects[@]}" | fzf --prompt='Project> ')"
    else
        echo "Projects:"
        select selection in "${projects[@]}" "Cancel"; do
            [[ "$selection" == "Cancel" ]] && return 1
            [[ -n "$selection" ]] && break
        done
    fi
    printf '%s' "$selection"
}

view_file() {
    local file="$1"
    [[ -f "$file" ]] || die "File not found: $file"

    if command -v glow >/dev/null 2>&1; then
        glow -p "$file"
    elif command -v bat >/dev/null 2>&1; then
        bat "$file"
    else
        "${PAGER_CMD:-less}" "$file"
    fi
}

edit_file() {
    local file="$1"
    mkdir -p "$(dirname "$file")"
    touch "$file"
    ${EDITOR_CMD:-vim} "$file"
}

timestamp() {
    date '+%Y%m%d-%H%M%S'
}

archive_existing() {
    local project="$1" file="$2"
    [[ -f "$file" ]] || return 0
    mkdir -p "$project/history"
    cp "$file" "$project/history/$(basename "${file%.md}")-$(timestamp).md"
}

assemble_theory_context() {
    local project="$1"
    local manifest="$project/context/theory-files.txt"
    [[ -f "$manifest" ]] || return 0

    while IFS= read -r rel; do
        [[ -z "$rel" || "$rel" == \#* ]] && continue
        local source="$THEORY_DIR/$rel"
        if [[ -f "$source" ]]; then
            printf '\n\n---\n\n# THEORY FILE: %s\n\n' "$rel"
            cat "$source"
        fi
    done < "$manifest"
}

run_ollama_stage() {
    local project="$1"
    local model="$2"
    local prompt_file="$3"
    local output_file="$4"
    shift 4
    local input_files=("$@")
    local prompt_log="$project/logs/$(timestamp)-$(basename "${output_file%.md}")-prompt.md"
    local run_log="$project/logs/$(timestamp)-$(basename "${output_file%.md}").log"
    local tmp
    tmp="$(mktemp)"

    {
        cat "$prompt_file"
        printf '\n\n# CANONICAL THEORY CONTEXT\n'
        assemble_theory_context "$project"
        for f in "${input_files[@]}"; do
            [[ -f "$f" ]] || continue
            printf '\n\n---\n\n# INPUT FILE: %s\n\n' "$(basename "$f")"
            cat "$f"
        done
    } > "$tmp"

    if [[ "${SAVE_RAW_PROMPTS:-true}" == "true" ]]; then
        cp "$tmp" "$prompt_log"
    fi

    archive_existing "$project" "$output_file"

    {
        echo "Model: $model"
        echo "Prompt: $prompt_file"
        echo "Output: $output_file"
        echo "Started: $(date --iso-8601=seconds)"
    } > "$run_log"

    echo
    echo "Running $model..."
    if [[ "${SHOW_MODEL_OUTPUT:-true}" == "true" ]]; then
        "$OLLAMA_BIN" run "$model" < "$tmp" | tee "$output_file"
        status=${PIPESTATUS[0]}
    else
        "$OLLAMA_BIN" run "$model" < "$tmp" > "$output_file"
        status=$?
    fi

    {
        echo "Finished: $(date --iso-8601=seconds)"
        echo "Exit status: $status"
        echo "Bytes: $(wc -c < "$output_file" 2>/dev/null || echo 0)"
        echo "Words: $(wc -w < "$output_file" 2>/dev/null || echo 0)"
    } >> "$run_log"

    rm -f "$tmp"
    return "$status"
}
