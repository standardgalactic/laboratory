#!/usr/bin/env bash

stage_output() {
    local project="$1" stage="$2"
    case "$stage" in
        classify) echo "$project/01-classification.md" ;;
        topic-analysis) echo "$project/02-topic-analysis.md" ;;
        outline) echo "$project/03-outline.md" ;;
        review-outline) echo "$project/04-outline-review.md" ;;
        draft) echo "$project/06-draft-1.md" ;;
        review-draft) echo "$project/07-draft-review.md" ;;
        revise) echo "$project/08-draft-2.md" ;;
        consistency) echo "$project/09-consistency-check.md" ;;
        finalize) echo "$project/10-final.md" ;;
        *) return 1 ;;
    esac
}

run_stage() {
    local project_name="$1" stage="$2"
    local project
    project="$(project_path "$project_name")"
    [[ -d "$project" ]] || die "Unknown project: $project_name"

    case "$stage" in
        classify)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/classify.md" \
                "$project/01-classification.md" \
                "$project/00-project.md" "$THEORY_DIR/categories.md"
            ;;
        topic-analysis)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/topic-analysis.md" \
                "$project/02-topic-analysis.md" \
                "$project/00-project.md" "$project/01-classification.md"
            ;;
        outline)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/outline.md" \
                "$project/03-outline.md" \
                "$project/00-project.md" "$project/01-classification.md" "$project/02-topic-analysis.md"
            ;;
        review-outline)
            run_ollama_stage "$project" "$REVIEWER_MODEL" \
                "$PROMPTS_DIR/review/review-outline.md" \
                "$project/04-outline-review.md" \
                "$project/00-project.md" "$project/03-outline.md"
            ;;
        draft)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/draft.md" \
                "$project/06-draft-1.md" \
                "$project/00-project.md" "$project/03-outline.md" "$project/04-outline-review.md" "$project/05-research-notes.md"
            ;;
        review-draft)
            run_ollama_stage "$project" "$REVIEWER_MODEL" \
                "$PROMPTS_DIR/review/review-draft.md" \
                "$project/07-draft-review.md" \
                "$project/00-project.md" "$project/03-outline.md" "$project/06-draft-1.md"
            ;;
        revise)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/revise.md" \
                "$project/08-draft-2.md" \
                "$project/00-project.md" "$project/06-draft-1.md" "$project/07-draft-review.md"
            ;;
        consistency)
            run_ollama_stage "$project" "$REVIEWER_MODEL" \
                "$PROMPTS_DIR/review/consistency.md" \
                "$project/09-consistency-check.md" \
                "$project/00-project.md" "$project/03-outline.md" "$project/07-draft-review.md" "$project/08-draft-2.md"
            ;;
        finalize)
            run_ollama_stage "$project" "$GENERATOR_MODEL" \
                "$PROMPTS_DIR/generation/finalize.md" \
                "$project/10-final.md" \
                "$project/00-project.md" "$project/08-draft-2.md" "$project/09-consistency-check.md"
            ;;
        *)
            die "Unknown stage: $stage"
            ;;
    esac
}
