#!/usr/bin/env bash

set -euo pipefail

MODELS=(
    "granite4.1:3b"
    "granite4.1:8b"
)

PROMPTS=(
    "Explain Rust ownership to an experienced C programmer."
    "Write a concise summary of general relativity in under 150 words."
    "Write a Python function that computes Fibonacci numbers using memoization."
    "Why are objects useful compressions of trajectories? Answer in three paragraphs."
    "Prove that the sum of the first n odd numbers equals n^2."
    "Describe the advantages and disadvantages of persistent data structures."
)

OUTDIR="ollama-benchmark-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTDIR"

echo "Results will be stored in $OUTDIR"
echo

for model in "${MODELS[@]}"; do
    echo "=================================================="
    echo "Testing $model"
    echo "=================================================="

    safe_model=$(echo "$model" | tr ':/' '__')

    i=1
    for prompt in "${PROMPTS[@]}"; do

        outfile="$OUTDIR/${safe_model}_test${i}.txt"

        echo
        echo "Test $i"
        echo "Prompt:"
        echo "$prompt"
        echo

        start=$(date +%s.%N)

        ollama run "$model" "$prompt" \
            > "$outfile"

        end=$(date +%s.%N)

        elapsed=$(awk "BEGIN {print $end-$start}")

        printf "Time: %.2f seconds\n" "$elapsed"

        echo "Saved to $outfile"

        {
            echo
            echo "------------------------------------------------------------"
            printf "Elapsed: %.2f seconds\n" "$elapsed"
            echo "------------------------------------------------------------"
        } >> "$outfile"

        ((i++))
    done

    echo
done

echo
echo "Benchmark complete."
