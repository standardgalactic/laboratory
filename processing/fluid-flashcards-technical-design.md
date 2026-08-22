# Fluid Flashcards

## Technical design, version 0.1

Status: implementation design, companion to the product specification
Date: 21 August 2026

This document specifies the SQLite schema, the domain-operation API, the scheduler boundary, and screen-by-screen interface behavior for Milestone One. It assumes the product specification (v0.1) as its source of requirements and does not restate rationale already established there.

---

## 1. Schema overview

The schema separates four concerns that the product specification keeps conceptually distinct: card content, organizational membership, learning state, and review history. No table couples more than one of these concerns. This is what makes the central invariant enforceable at the storage layer rather than only in application code: a card row never contains a collection reference, and a learning-state row never contains organizational data.

All tables use `TEXT` UUIDs (v7, time-ordered) as primary keys, except append-only event tables which additionally carry a monotonically increasing integer `seq` for cheap ordering. Timestamps are stored as ISO-8601 UTC strings. Foreign keys are declared `ON DELETE RESTRICT` by default; the few intentional cascades are called out below.

### 1.1 `cards`

```sql
CREATE TABLE cards (
    id              TEXT PRIMARY KEY,
    status          TEXT NOT NULL CHECK (status IN ('active','suspended','archived')) DEFAULT 'active',
    front           TEXT NOT NULL,
    back            TEXT NOT NULL,
    notes           TEXT,
    provenance      TEXT,           -- e.g. 'memrise-import:2026-08-21', 'manual'
    fields_json     TEXT,           -- reserved for future named fields beyond front/back
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
) STRICT;

CREATE INDEX idx_cards_status ON cards(status);
```

`fields_json` exists so a later card type (e.g. cloze, audio-prompt) can add fields without an entity migration, per spec §5.1. Milestone One writes it as `NULL` and does not read it.

### 1.2 `tags` and `card_tags`

```sql
CREATE TABLE tags (
    id      TEXT PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE COLLATE NOCASE
) STRICT;

CREATE TABLE card_tags (
    card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    tag_id  TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, tag_id)
) STRICT;

CREATE INDEX idx_card_tags_tag ON card_tags(tag_id);
```

Tag deletion cascades to `card_tags` (removing the label), never to `cards`.

### 1.3 `collections` and `levels`

```sql
CREATE TABLE collections (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('active','archived')) DEFAULT 'active',
    source_kind TEXT NOT NULL CHECK (source_kind IN ('manual','saved_mix','materialized')) DEFAULT 'manual',
    mix_def_json TEXT,      -- present only when source_kind = 'saved_mix'; see §1.7
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
) STRICT;

CREATE TABLE levels (
    id              TEXT PRIMARY KEY,
    collection_id   TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    ordinal         INTEGER NOT NULL,   -- display order within the collection
    UNIQUE (collection_id, ordinal)
) STRICT;
```

A `saved_mix` collection stores its defining selection in `mix_def_json` and has no rows in `memberships`; its contents are computed on read (§1.7). A `materialized` collection is a normal membership-backed collection that happened to be created by flattening a mix result — the distinction is provenance metadata only, not a structural difference from `manual`.

### 1.4 `memberships`

```sql
CREATE TABLE memberships (
    id              TEXT PRIMARY KEY,
    card_id         TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    collection_id   TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    level_id        TEXT REFERENCES levels(id) ON DELETE SET NULL,
    position        INTEGER,            -- ordering within (collection, level); NULL = unordered
    created_at      TEXT NOT NULL,
    UNIQUE (card_id, collection_id)
) STRICT;

CREATE INDEX idx_memberships_card ON memberships(card_id);
CREATE INDEX idx_memberships_collection ON memberships(collection_id, level_id, position);
```

A card occupies at most one level within a given collection — `level_id` is a field on the membership, not a second axis of identity. `UNIQUE (card_id, collection_id, level_id)` was wrong: SQLite treats `NULL` as distinct from every other value in a unique index, so it would have permitted unlimited duplicate unlevelled memberships for the same card, and it would have permitted the same card to sit in several levels of one collection simultaneously by inserting several level-bearing rows. `UNIQUE (card_id, collection_id)` closes both holes. Moving a card between levels of the same collection is therefore an `UPDATE` of `level_id` on the existing row, not an insert of a new one (see the revised `move_membership`, §2.2).

This is the table that realizes "collections only select cards": it carries no scheduling fields, no review counters, nothing that `card_review_state` also owns. Deleting a membership row is the entirety of "removing a card from a collection." Deleting a card cascades memberships, which is correct — the card is gone — but deleting a *collection* also cascades memberships while leaving the card and its learning state untouched, which is the specific behavior spec §5.2 requires.

### 1.5 `card_review_state`

```sql
CREATE TABLE card_review_state (
    card_id             TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    direction           TEXT NOT NULL CHECK (direction IN ('front_to_back','back_to_front')),
    due_at              TEXT,
    stability           REAL,
    difficulty          REAL,
    interval_days       REAL,
    lapse_count         INTEGER NOT NULL DEFAULT 0,
    success_count       INTEGER NOT NULL DEFAULT 0,
    last_grade          TEXT,
    last_reviewed_at    TEXT,
    scheduler_version   TEXT NOT NULL,   -- e.g. 'fsrs-4.5'
    PRIMARY KEY (card_id, direction)
) STRICT;

CREATE INDEX idx_review_state_due ON card_review_state(due_at);
```

One row per `(card, direction)` per spec §5.3. This table is read by every collection a card belongs to and is written only by `submit_review` and `reset_learning_state` — never by any organizational operation. `scheduler_version` is stored per row (not globally) so a scheduler migration can be applied incrementally and audited.

### 1.6 `review_events`

```sql
CREATE TABLE review_events (
    seq                 INTEGER PRIMARY KEY AUTOINCREMENT,
    id                  TEXT NOT NULL UNIQUE,
    card_id             TEXT NOT NULL REFERENCES cards(id) ON DELETE RESTRICT,
    direction           TEXT NOT NULL,
    session_id          TEXT NOT NULL REFERENCES sessions(id) ON DELETE RESTRICT,
    prompt_shown        TEXT NOT NULL,
    response_text       TEXT,
    grade               TEXT NOT NULL,
    response_time_ms    INTEGER,
    state_before_json   TEXT NOT NULL,
    state_after_json    TEXT NOT NULL,
    voided              INTEGER NOT NULL DEFAULT 0 CHECK (voided IN (0,1)),
    void_reason         TEXT,
    created_at          TEXT NOT NULL
) STRICT;

CREATE INDEX idx_review_events_card ON review_events(card_id, direction, created_at);
CREATE INDEX idx_review_events_session ON review_events(session_id);
```

Append-only: no `UPDATE` touches any column except `voided`/`void_reason`, and application code enforces this (SQLite has no per-column write trigger cheap enough to bother with here; a `BEFORE UPDATE` trigger rejecting changes to any other column is included for defense in depth — see §1.9). `ON DELETE RESTRICT` on `card_id` means a card with review history cannot be hard-deleted; it can only be archived. This is deliberate: spec §5.4 requires editing organization to never rewrite review events, and the strongest guarantee of that is making the events outlive the possibility of accidental card deletion.

### 1.7 `views` (saved Boolean filters) and mix definitions

```sql
CREATE TABLE views (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    filter_json TEXT NOT NULL,     -- see filter grammar below
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
) STRICT;
```

`filter_json` and `mix_def_json` (from `collections.mix_def_json`) share one grammar. A flat `sources` list combined with a flat `predicates` list — as an earlier draft of this design proposed — can express `(sources) AND (predicates)` but not an arbitrary Boolean expression such as `(Arabic AND verbs) OR (Greek AND weak)`, and cannot negate a compound sub-expression at all. Spec §10 requires AND/OR/NOT composable and savable, so the grammar is a recursive node tree instead:

```json
{
  "node": "any",
  "children": [
    {
      "node": "all",
      "children": [
        {"node": "source", "type": "tag", "id": "arabic-tag-id"},
        {"node": "source", "type": "tag", "id": "verbs-tag-id"}
      ]
    },
    {
      "node": "all",
      "children": [
        {"node": "source", "type": "tag", "id": "greek-tag-id"},
        {"node": "predicate", "field": "mastery_band", "op": "=", "value": "weak"}
      ]
    }
  ]
}
```

Node types: `source` (leaf — `collection`, `level`, `tag`, `view`, or an explicit `cards: [ids]` list), `predicate` (leaf — a field/op/value test such as `status = active` or `direction_due before now`), `all` (AND over children), `any` (OR over children), and `not` (single child, negated). `evaluate_view` walks this tree once into a card-id set; there is no separate `combinator`/`predicate_combinator` split, and no special-cased `not_in` predicate operator standing in for general negation — negation is a node like any other and can wrap a compound sub-expression. A view and a mix definition are the same object under this grammar; a `collections` row of `source_kind = 'saved_mix'` is simply a named, persisted, re-evaluated view whose evaluated card set the UI presents like any other collection.

Milestone One's Mix builder screen (§4.3) only ever constructs the shallow shape — one `any` of `source` leaves, optionally wrapped in one `all` with a handful of `predicate` leaves — matching spec §17's decision to defer the general view-builder UI. The recursive grammar exists in the schema and the evaluator now so that Milestone Two's Boolean-view builder is a new screen over the same `filter_json`, not a data migration.

### 1.8 `sessions`

```sql
CREATE TABLE sessions (
    id              TEXT PRIMARY KEY,
    selection_json  TEXT NOT NULL,     -- the resolved snapshot, not a live reference
    mixing_policy   TEXT NOT NULL,
    study_mode      TEXT NOT NULL CHECK (study_mode IN ('typed','self_graded')),
    seed            INTEGER NOT NULL,
    card_count      INTEGER NOT NULL,
    duplicates_collapsed INTEGER NOT NULL DEFAULT 0,
    started_at      TEXT NOT NULL,
    completed_at    TEXT
) STRICT;

CREATE TABLE session_queue (
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    position    INTEGER NOT NULL,
    card_id     TEXT NOT NULL REFERENCES cards(id) ON DELETE RESTRICT,
    direction   TEXT NOT NULL,
    PRIMARY KEY (session_id, position)
) STRICT;
```

`selection_json` freezes the resolved card-id list (not the view definition) at generation time, satisfying spec §7's requirement that the queue is stable unless explicitly regenerated, and that a seed makes a shuffle reproducible. `session_queue` is the materialized, ordered result — the thing the study screen actually walks. `study_mode` records typed vs. self-graded recall for the session as a whole (Milestone One does not support per-card mode within one session) — an earlier draft of this design left this unstored even though the study screen dispatches on it; the walkthrough that exercises this design end to end is what surfaced the omission.

### 1.9 Integrity triggers

```sql
CREATE TRIGGER trg_review_events_immutable
BEFORE UPDATE OF card_id, direction, session_id, prompt_shown, response_text,
                 grade, response_time_ms, state_before_json, state_after_json,
                 created_at ON review_events
BEGIN
    SELECT RAISE(ABORT, 'review_events rows are append-only except voided/void_reason');
END;
```

### 1.10 Import tables

```sql
CREATE TABLE card_external_ids (
    card_id     TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    namespace   TEXT NOT NULL,      -- e.g. 'memrise-course-4821', one per import source
    external_id TEXT NOT NULL,
    PRIMARY KEY (card_id, namespace),
    UNIQUE (namespace, external_id)
) STRICT;

CREATE TABLE import_batches (
    id              TEXT PRIMARY KEY,
    source_format   TEXT NOT NULL CHECK (source_format IN ('csv','tsv')),
    field_mapping_json TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('staged','committed','rolled_back')) DEFAULT 'staged',
    created_at      TEXT NOT NULL,
    committed_at    TEXT
) STRICT;

CREATE TABLE import_rows (
    id              TEXT PRIMARY KEY,
    batch_id        TEXT NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
    row_number      INTEGER NOT NULL,
    raw_json        TEXT NOT NULL,
    classification  TEXT NOT NULL CHECK (classification IN
                       ('new','exact_duplicate','probable_duplicate','update_match','malformed','missing_required')),
    resolved_action TEXT CHECK (resolved_action IN ('create','skip','update','create_anyway')),
    resulting_card_id  TEXT REFERENCES cards(id),
    card_before_json   TEXT   -- populated only when resolved_action = 'update';
                               -- the full pre-existing card row, for rollback
) STRICT;
```

`update_match` classification is computed by joining the row's mapped external-identifier column against `card_external_ids(namespace, external_id)` for the batch's namespace (typically the batch id, or a caller-supplied namespace for re-importing the same external source under a stable key). A row with no match on that join and no exact/probable content match is `new`; committing it also inserts its `card_external_ids` row so later re-imports can match it.

Before `commit_import` applies an `update` action to a pre-existing card, it snapshots that card's current `front`/`back`/`notes`/`tags` into `card_before_json` on the same `import_rows` row, in the same transaction as the write. This is what makes rollback of an update possible at all — without a before-image there is nothing to restore.

Rollback of a `committed` batch, per row: for `create` actions, delete the card if it has zero rows in `review_events`, else archive it with a note (never delete a card with history). For `update` actions, restore `front`/`back`/`notes`/`tags` from `card_before_json` — the card itself is never deleted, since it predates the batch by definition. This is how spec §11's "without affecting later review history for pre-existing cards" is honored even for cards the rolled-back import touched via `update_match`: their review state and event history are untouched by either the update or its rollback, only the four content fields move.

### 1.11 Full-text search index

```sql
CREATE VIRTUAL TABLE cards_fts USING fts5(
    front, back, notes,
    content='cards', content_rowid='rowid'
);

CREATE TRIGGER trg_cards_fts_insert AFTER INSERT ON cards BEGIN
    INSERT INTO cards_fts(rowid, front, back, notes)
    VALUES (new.rowid, new.front, new.back, new.notes);
END;

CREATE TRIGGER trg_cards_fts_update AFTER UPDATE OF front, back, notes ON cards BEGIN
    INSERT INTO cards_fts(cards_fts, rowid, front, back, notes)
    VALUES ('delete', old.rowid, old.front, old.back, old.notes);
    INSERT INTO cards_fts(rowid, front, back, notes)
    VALUES (new.rowid, new.front, new.back, new.notes);
END;

CREATE TRIGGER trg_cards_fts_delete AFTER DELETE ON cards BEGIN
    INSERT INTO cards_fts(cards_fts, rowid, front, back, notes)
    VALUES ('delete', old.rowid, old.front, old.back, old.notes);
END;
```

The library search (§4.2) queries `cards_fts` directly for the `front`/`back`/`notes` portion of spec §10's search scope and joins back to `cards`/`tags`/`collections` for the rest (tag names, collection names, levels, provenance — ordinary indexed equality/prefix lookups, not FTS). Keeping the sync triggers in the schema rather than only describing FTS as a screen-level detail is what makes the 100ms search target (spec §16) a property the database enforces rather than something the application layer has to remember to maintain.

### 1.12 `settings`

```sql
CREATE TABLE settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
) STRICT;
```

Key-value; holds schema version, backup directory, keyboard-shortcut overrides, daily-limit defaults, and scheduler parameter set. `schema_version` here is the source of truth checked against `PRAGMA user_version` on startup.

---

## 2. Domain operations

The backend exposes only the operations below; nothing else may mutate the database. Each is a single transaction. Signatures are given as TypeScript-flavored pseudocode over the Rust service boundary; exact serialization is JSON over a local HTTP or IPC channel, not specified further here.

### 2.1 Card operations

```
create_card(front, back, notes?, tags?, provenance?) -> Card
update_card(card_id, patch: {front?, back?, notes?, tags?}) -> Card
  # Never touches card_review_state or review_events. Editing wording
  # does not reset scheduling (spec §6, §9).
set_card_status(card_id, status: active|suspended|archived) -> Card
delete_card(card_id) -> Result<(), Error>
  # Rejected if review_events exist for card_id (ON DELETE RESTRICT).
  # The UI should offer archive as the alternative and explain why.
reset_learning_state(card_id, direction) -> Result<(), Error>
  # The ONLY operation permitted to zero out card_review_state.
  # Requires explicit confirmation in the UI; never called by any
  # other operation in this list.
```

### 2.2 Membership operations

```
add_membership(card_id, collection_id, level_id?, position?) -> Membership
  # Upsert on (card_id, collection_id): if a membership already exists
  # in that collection, this updates its level_id/position in place
  # rather than erroring or inserting a duplicate.
remove_membership(membership_id) -> Result<(), Error>
move_membership(membership_id, to_collection_id, to_level_id?) -> Membership
  # Same collection, different level: UPDATE level_id/position on the
  # existing row (no new membership id).
  # Different collection: add_membership(destination) +
  # remove_membership(source) in one transaction, as before.
bulk_add_membership(card_ids[], collection_id, level_id?) -> Membership[]
bulk_remove_membership(membership_ids[]) -> Result<(), Error>
```

### 2.3 Collection operations

```
create_collection(name, source_kind: manual) -> Collection
rename_collection(collection_id, name) -> Collection
duplicate_collection_structure(collection_id, new_name) -> Collection
  # Copies levels and memberships (same card_ids, new membership rows).
  # Copies zero cards, zero review state.
archive_collection(collection_id) -> Collection
delete_collection(collection_id) -> Result<(), Error>
  # Cascades memberships only. Cards and card_review_state are untouched.
  # Requires a preview (see 2.6) accepted by the caller before executing.
merge_collections(source_ids[], mode: 'saved_mix'|'materialize', new_name) -> Collection
split_collection(collection_id, rule: ByLevel|ByTag|BySearch|BySelection|ByFixedSize,
                  replace_source: bool) -> Collection[]
```

### 2.4 View / mix operations

```
create_view(name, filter: FilterDef) -> View
update_view(view_id, filter: FilterDef) -> View
evaluate_view(filter: FilterDef) -> {card_id: CardId, match_count: int}[]
  # Pure read; used both to render a view/mix live and to produce
  # the snapshot consumed by generate_session. Returns per-card
  # match counts, not a bare deduplicated set — generate_session
  # needs the counts to compute duplicates_collapsed (a card matched
  # by two selected sources has match_count = 2). Screens that just
  # want the eligible card set use the keys and ignore the counts.
```

### 2.5 Session / study operations

```
generate_session(selection: FilterDef, policy: MixingPolicy, study_mode: 'typed'|'self_graded',
                  seed?, size_limit?) -> Session
  # 1. evaluate_view(selection) -> {card_id, match_count}[] (snapshot)
  # 2. duplicates_collapsed = sum(match_count) - count(distinct card_id)
  # 3. apply policy (full_shuffle | proportional | equal_source |
  #    interleave | weakest_first | due_first) with seed
  #    NOTE: source attribution for a card matched by more than one
  #    selected source, direction assignment per card, in-policy
  #    queue ordering, and exhaustion behavior (size_limit exceeds
  #    the pool, an empty source, due-first running out of due
  #    cards) are NOT specified by this design — see the mixing-
  #    policy document for the precise algorithms.
  # 4. persist sessions + session_queue rows
  # Returns the session with its ordered queue and the
  # duplicates_collapsed count for the preview UI (spec §7).

submit_review(session_id, card_id, direction, grade, response_text?,
              response_time_ms?) -> ReviewResult
  # One transaction:
  #   a. read card_review_state(card_id, direction) as state_before
  #   b. call scheduler.next_state(state_before, grade)  [§3]
  #   c. write card_review_state = state_after
  #   d. insert review_events row with state_before_json/state_after_json
  # Both (c) and (d) commit together or not at all (spec §15).

end_session(session_id) -> Session  # sets completed_at

void_review_event(event_id, reason) -> Result<(), Error>
  # Only permitted when event_id is the MOST RECENT non-voided event
  # for its (card_id, direction) — checked via idx_review_events_card.
  # Voiding an older event and leaving later events in place would
  # make current card_review_state causally dependent on a review
  # the audit trail now says never happened, with no way to know
  # what the later events "should" have been instead. Rejecting
  # anything but the latest event is Milestone One's rule; replaying
  # every later event through the scheduler to support arbitrary
  # historical void is deferred, not silently assumed.
  # On success: sets voided=1, restores card_review_state to
  # state_before_json from the same row. Never deletes the row.

migrate_scheduler(card_ids[], to_version) -> Result<(), Error>
  # See §3. Writes new card_review_state rows and one 'migration'
  # review_events row per card, in one transaction per card.
```

### 2.6 Preview / destructive-operation support

```
preview_deletion(target: Collection|Card|Membership[]) -> {
  affected_cards: CardId[],
  affected_memberships: Membership[],
  affected_review_events_count: int,
  cards_blocked_from_deletion: CardId[]   # have review history
}
```

Every operation in §2.3 and §2.1 marked destructive calls this first and requires the caller (UI) to display and accept the result, per spec §6.

### 2.7 Import/export operations

```
stage_import(file_bytes, format: csv|tsv, mapping: FieldMapping) -> ImportBatch
  # Classifies every row; writes import_rows; commits nothing to
  # cards/memberships yet.
resolve_import_row(row_id, action: create|skip|update|create_anyway) -> ImportRow
commit_import(batch_id) -> ImportBatch
  # Applies resolved_action for every row in one transaction;
  # sets resulting_card_id on each row.
rollback_import(batch_id) -> Result<(), Error>
  # See §1.10 for the archive-instead-of-delete rule.

export_archive(target_path) -> ExportManifest
  # Full JSON archive, sufficient to reconstruct an equivalent
  # database (spec §11): cards, memberships, levels, collections,
  # card_external_ids, views, card_review_state, review_events,
  # sessions, session_queue, import_batches, import_rows, settings,
  # schema_version. sessions/session_queue MUST be included:
  # review_events.session_id is a foreign key against sessions, so
  # an archive omitting sessions cannot be restored without either
  # a foreign-key violation or silently orphaned review history.
  # card_external_ids MUST be included so a re-import after restore
  # still resolves update_match instead of reclassifying everything
  # as new.
export_selection_csv(filter: FilterDef, target_path) -> Result<(), Error>
```

### 2.8 Settings and backup operations

The design principle that "the backend must expose domain operations rather than raw table mutation" (spec §15) applies to `settings` exactly as it does to every other table; the earlier draft's description of the settings screen writing rows directly contradicted that principle and is corrected here and in §4.8.

```
update_settings(patch: {key: value, ...}) -> Settings
  # Validates known keys (backup_directory, daily_limit_default,
  # keyboard_shortcuts_json, default_scheduler_version, ...);
  # unknown keys are rejected rather than silently stored.
create_backup(reason: 'migration'|'destructive_op'|'manual') -> BackupManifest
  # Called automatically before any migration and before any
  # operation §2.6's preview marks destructive; also callable
  # directly from the settings screen.
restore_backup(backup_id) -> Result<(), Error>
  # Replaces the live database file with the chosen backup after
  # taking one more automatic backup of the pre-restore state.
```

---

## 3. Scheduler boundary

The scheduler is isolated behind one trait so Milestone One's FSRS-vs-simple-interval comparison (spec §17) is a swap, not a rewrite.

```rust
trait Scheduler {
    fn version(&self) -> &str;               // e.g. "fsrs-4.5"

    fn initial_state(&self) -> SchedulerState;

    fn next_state(
        &self,
        current: &SchedulerState,
        grade: Grade,                          // Again | Hard | Good | Easy
        reviewed_at: DateTime<Utc>,
    ) -> SchedulerState;
}

struct SchedulerState {
    due_at: Option<DateTime<Utc>>,
    stability: Option<f64>,
    difficulty: Option<f64>,
    interval_days: Option<f64>,
    lapse_count: u32,
    success_count: u32,
}
```

Constraints on any implementation:

- `next_state` is a pure function of `(current, grade, reviewed_at)` — no database access, no hidden global state, no side effects. This is what lets `submit_review` (§2.5) treat it as a single in-transaction call and what lets `state_before_json`/`state_after_json` in `review_events` fully reconstruct scheduler behavior for audit or replay.
- `version()` is written into every `card_review_state` row it touches. Two schedulers may coexist in one database (a migration in progress); a session may mix cards at different `scheduler_version`s, and the UI is not required to hide this, only to never silently rewrite a card's version without a review.
- Because coexistence is allowed, `submit_review` cannot simply call "the active scheduler." A `SchedulerRegistry` maps `scheduler_version -> Box<dyn Scheduler>`, populated at startup from every version this build knows how to run. `submit_review` reads `card_review_state.scheduler_version` for the row it is about to update, looks up that exact implementation in the registry, and calls `next_state` on it — never the version named in `settings`. If a version appears in a row but not in the registry (an old database opened by a build that dropped support for it), `submit_review` fails closed with an explicit error rather than silently reinterpreting the state under a different scheduler's semantics.
- For a card with no `card_review_state` row yet in a given direction (first review ever), `submit_review` calls `initial_state()` on the scheduler named in `settings.default_scheduler_version` and stamps the new row with that version — this is the one place `settings` determines scheduler choice.
- Moving a card from one scheduler version to another is not implicit in any review; it is a separate, explicit `migrate_scheduler(card_ids[], to_version)` operation (§2.5) that computes each card's new `SchedulerState` via a version-pair-specific conversion function (not a fresh `initial_state()`, which would discard history) and writes it in one transaction per card, logging the change as a `review_events` row with `grade = 'migration'` so the audit trail shows the version boundary rather than an unexplained discontinuity in interval or stability.
- Milestone One ships two implementations behind this trait — a minimal FSRS port and a fixed-multiplier interval scheduler — selected per spec §17's criterion (transparent, stable behavior across imported history). The comparison harness replays a fixed set of imported review histories through both and reports interval drift and lapse-rate stability, not configurability.
- `weakest-first` mixing (spec §7) reads `stability`/`difficulty` off `card_review_state` to estimate recall probability. This estimate is scheduler-specific; the mixing-policy code calls a second trait method, `fn recall_probability(&self, state: &SchedulerState, at: DateTime<Utc>) -> f64`, rather than reimplementing FSRS's forgetting curve in the mixing layer.

---

## 4. Screen-by-screen interface behavior

### 4.1 Home

Three panels: card library (left), collections with visible level sequences (center), a persistent Study button. Each collection tile shows total cards, cards due, and a Memrise-style level strip (unseen/learning/familiar/mastered proportions per spec §4) computed from `card_review_state` joined through `memberships` — never stored redundantly on the collection.

Selecting one collection tile and pressing Study calls `generate_session` with that collection as the sole source and `due_first` as the default policy. Selecting two or more tiles (via checkbox, not click-to-open) replaces the Study button with a Mix button; pressing it opens 4.3.

### 4.2 Card library / search

A single scrollable, virtualized list (required for the 30,000-card performance target, spec §16) backed by `evaluate_view`. The search box updates the underlying filter's `predicate`/`source` nodes on a short debounce; results must visibly update within 100ms per spec §16, which constrains the query to indexed columns and the `cards_fts` virtual table (§1.11).

Row actions match spec §10 exactly: Select all, Select visible, invert selection, add membership, remove membership, tag, suspend, archive, export, Study. All are available from one persistent action bar that activates once selection is non-empty; none require opening a card.

### 4.3 Mix builder

Opens with the calling selection pre-populated as `sources`. Controls: a source list (removable chips, each showing its resolved card count), a combinator toggle (OR/AND for sources — spec §10), a predicate row for status/direction/due-state/tag filters, and a policy selector limited to the six values in spec §7. A live count ("1,842 cards, 214 due") updates on every change via `evaluate_view`, distinct from the eventual session size (which `size_limit` may cap).

Pressing "Start" calls `generate_session`. Before entering the study screen, a lightweight interstitial reports `duplicates_collapsed` if nonzero ("214 cards appeared in more than one selected source and were shown once") — this satisfies spec §7's preview requirement without a full modal for the common case.

Pressing "Save as mix" instead calls `create_view`/`collections` with `source_kind='saved_mix'` and the current `FilterDef`, then returns to Home with the new tile visible.

### 4.4 Study screen

Single-purpose, minimal-chrome, per spec §13 (no unnecessary animation or layout movement). Displays one card from `session_queue` at a time in the mode(s) configured for that session. Milestone One ships typed and self-graded recall only, matching spec §17's milestone scope; multiple choice is part of the product's eventual study-mode set (spec §8) but is not implemented — not even behind a manual-distractor path — until its schema exists (see §5). The study screen's mode dispatch is written as an open `match` over a `StudyMode` enum so adding `MultipleChoice` later is a new arm, not a rewrite of the screen.

- Typed mode: input box, Enter submits; grading applies Unicode NFC normalization, configurable case-fold, whitespace collapse, and optional diacritic-tolerant comparison before showing correct/incorrect, and the learner's raw input remains visible next to the accepted answer.
- Self-graded mode: reveal button, then four grade buttons (Again/Hard/Good/Easy) with visible keyboard shortcuts (1–4) that can be hidden once a per-user "shortcuts learned" flag is set in `settings`.

Every submission calls `submit_review` synchronously before advancing the queue pointer; the screen does not optimistically advance, so a transaction failure is visible immediately rather than silently lost. RTL text (spec §13) is rendered with `dir="auto"` per field with a manual override stored on the card if auto-detection is wrong.

### 4.5 Card editor

Opens as an inline panel/modal over the current screen, never a navigation. After saving, focus returns to a fresh blank editor if the entry point was "create," so a rapid run of card creation (spec §4) requires no repeated navigation — Tab/Enter chains through front, back, tags, save, next.

The editor does not include a multiple-choice distractor field or preview in Milestone One, for the same reason given in §4.4: no distractor schema exists yet. This is a change from an earlier draft of this design, which described the schema as already covering distractors — it did not; `cards.fields_json` is written as `NULL` and unread in Milestone One, and no distractor or pool table exists (see §5).

### 4.6 Collection / level view

Ordered list of levels, each expandable to its member cards (via `memberships` filtered by `level_id`, ordered by `position`). Drag-and-drop between levels calls `move_membership` when dropped inside the same collection tree, and `add_membership` (leaving the source intact) when dragged from the library or another collection — matching spec §6's default-add / explicit-move distinction. A visible mode toggle ("Add" vs "Move") sits above the drop target so the two behaviors are never ambiguous to the user mid-drag.

Structural duplication, merge, and split (spec §6) are reached from a collection's overflow menu, each routing to `duplicate_collection_structure`, `merge_collections`, or `split_collection`, each gated by the §2.6 preview for any variant that removes source memberships (`replace_source: true` on split, or "Move" mode on drag).

### 4.7 Import wizard

Three fixed steps: file + delimiter detection, field-mapping (source columns to front/back/notes/tags/collection/level/external_id, plus a `distractors` column that the mapper accepts per spec §11 but that `commit_import` retains only inside `raw_json` — there is no table to write it into yet, per §5), and a classification review table (new / exact duplicate / probable duplicate / update match / malformed / missing required, per spec §11) with a bulk-then-override action per classification bucket. `stage_import` runs after mapping is confirmed; nothing commits until the review table's choices are confirmed and `commit_import` is called. A visible batch id and a "roll back this import" action remain available from the collection the import targeted, for as long as `import_batches.status = 'committed'`.

### 4.8 Export / settings

Export screen offers "Full archive (JSON)" and "Selection (CSV/TSV)," mapping directly to `export_archive` and `export_selection_csv`; no other export path exists, satisfying spec §11's "no proprietary format may be the sole export path" by construction rather than by choice architecture. Settings screen edits (backup directory, daily limits, keyboard shortcuts, default scheduler version) go through `update_settings` (§2.8), not a direct table write — this screen is bound by the same "domain operations only" rule as every other screen in this document. A manual "Back up now" action calls `create_backup` directly; a "Restore from backup" action lists backups (created automatically before migrations and destructive bulk operations, per spec §12, and manually on request) and calls `restore_backup`.

---

## 5. Cross-cutting notes for Milestone One

Boolean saved views and Milestone One's study modes split differently than an earlier draft of this design claimed, and it is worth being precise about which is which:

- **Boolean views/mixes (§1.7)** *are* fully scoped in the schema now — the recursive `filter_json` grammar and `evaluate_view` support arbitrary AND/OR/NOT today — with only the general view-builder UI deferred to Milestone Two per spec §17. This one is genuinely schema-ready, UI-deferred.
- **Multiple choice and distractors (§4.4, §4.5)** are *not* scoped in the schema. No distractor table, pool-query definition, or manual-distractor field exists anywhere in §1; `cards.fields_json` is reserved but unwritten. Multiple choice is entirely out of Milestone One — not just its UI — and its schema (a `distractors` table keyed on `card_id`, plus whatever pool-eligibility rule the product spec's "no shared wording or definition substring" requirement turns into) is deferred design work, not a hidden feature waiting on a UI. Treating it as already schema-ready in the first draft of this document was a mistake worth naming rather than quietly fixing.

The Milestone One walkthrough (companion document, "Fluid Flashcards: Milestone One walkthrough") traced a concrete scenario through card creation, import with update-match and rollback, mixed-session generation, first review, and full export. It found and this document now reflects three fixes — `evaluate_view` returning per-card match counts rather than a bare deduplicated set, a `study_mode` column on `sessions`, and `export_archive` including `sessions`/`session_queue`/`card_external_ids`/`import_batches`/`import_rows` (the first of those was a referential-integrity bug: `review_events.session_id` had nothing to restore against without it). It also surfaced four open questions that `generate_session` and the mixing policies of spec §7 do not yet answer — source attribution when a card matches more than one selected source, direction assignment per card, in-policy queue ordering, and exhaustion behavior — none of which block Milestone One's schema, but all of which block writing the mixing-policy document that comes next.

The scheduler comparison (§3) and the 30,000-card import/search/session performance targets (spec §16) are the two items in this design most likely to force a schema revision; both are called out here so a revision, if needed, is scoped to `card_review_state` and the FTS index rather than the membership or event tables.
