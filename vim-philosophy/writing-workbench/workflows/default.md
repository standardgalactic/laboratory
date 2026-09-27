# Default Workflow

classify -> topic-analysis -> outline -> review-outline -> draft -> review-draft -> revise -> consistency -> finalize

Generation stages use the generator model.

Review stages use the reviewer model.

Each successful stage writes a timestamped copy to `history/` before updating the current stage file.
