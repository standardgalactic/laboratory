# Fluid Flashcards

## Milestone One walkthrough

Status: verification document, exercises the technical design (v0.1) as one system
Date: 21 August 2026

This document traces one concrete scenario through every layer of the technical design — schema, domain operations, scheduler boundary, and screens — from card creation and import through a mixed session, a first review, and a full export. The goal is not to demonstrate the system working; it is to find the places where two parts of the design assume different things about a third. Findings are collected in §7, split into what was wrong and got fixed, versus what is genuinely unresolved and belongs to the next document (mixing-policy formalization).

Row values below are illustrative and shortened for readability (`crd_bayt` rather than a real UUIDv7); every id in an actual system is the UUID the schema specifies.

---

## 1. Starting state

A collection already exists from prior use:

- `collections`: `col_basics` — "Arabic Basics", `source_kind = 'manual'`
- `levels`: `lvl_1` — "Level 1", `collection_id = col_basics`, `ordinal = 1`
- `cards`: `crd_bayt` — front `بيت`, back `house`, `status = 'active'`
- `memberships`: `mem_001` — `(card_id: crd_bayt, collection_id: col_basics, level_id: lvl_1)`
- No `card_review_state` row for `crd_bayt` in either direction — it has never been studied.

## 2. Creating a card manually

`create_card(front: "ماء", back: "water") -> crd_maa` inserts one `cards` row and nothing else — no membership, no review state, per §2.1. The learner then places it:

`add_membership(card_id: crd_maa, collection_id: col_basics, level_id: lvl_1) -> mem_002`

Per the revised §1.4/§2.2 upsert rule, this is a plain insert here (no prior membership for this `(card_id, collection_id)` pair exists), giving:

| id | card_id | collection_id | level_id | position |
|---|---|---|---|---|
| mem_001 | crd_bayt | col_basics | lvl_1 | — |
| mem_002 | crd_maa | col_basics | lvl_1 | — |

No gap found here — the card-editor rapid-creation flow (§4.5) and the upsert semantics agree cleanly.

## 3. Importing a second collection

The learner creates `col_verbs` ("Arabic Verbs", manual) and imports a three-row CSV mapped to `front`, `back`, `external_id` (namespace `arabic-verbs-2024`).

**Staging** (`stage_import`) classifies each row against `cards` and `card_external_ids`:

| row | front | back | external_id | classification |
|---|---|---|---|---|
| 1 | كتب | wrote | mem-verb-014 | `new` (no match on content or `card_external_ids`) |
| 2 | بيت | house | mem-verb-015 | `exact_duplicate` (content matches `crd_bayt`) |
| 3 | شرب | *(blank)* | mem-verb-016 | `missing_required` (`back` is empty) |

**Resolution:** the learner accepts row 1 (`create`), skips row 2 (`skip` — already has this word), and skips row 3 (`skip` — nothing to correct it against; the wizard offers per-classification bulk action, not inline row editing, matching spec §11's "the learner chooses the action for each category" rather than promising a row-level editor Milestone One doesn't have).

**Commit** (`commit_import`) applies row 1 only:

- `cards`: `crd_kataba` — front `كتب`, back `wrote`, `provenance = 'import:batch_01'`
- `card_external_ids`: `(crd_kataba, 'arabic-verbs-2024', 'mem-verb-014')`
- `memberships`: `mem_003` — `(crd_kataba, col_verbs, level_id: NULL)`
- `import_rows.row[1].resulting_card_id = crd_kataba`; rows 2 and 3 keep `resulting_card_id = NULL`, `card_before_json = NULL` (no update happened, so no before-image is needed — that column is exercised only in §3.1 below).

### 3.1 Exercising the update-match / rollback path

Later, the learner re-imports a corrected version of the same source with the same namespace. Row 1 of the new batch has `external_id: mem-verb-014` (matches `card_external_ids`) but `back: "wrote / has written"` (content differs). Classification is `update_match`. On `commit_import` with `resolved_action = 'update'`:

- `import_rows.card_before_json` is set to `{"front": "كتب", "back": "wrote", "notes": null, "tags": []}` — the pre-update snapshot — in the **same transaction** as the write to `cards.back`.
- `cards.back` becomes `"wrote / has written"`; `updated_at` advances; `card_review_state` and `review_events` for `crd_kataba` (there are none yet at this point in the scenario) are untouched, confirming §1.10's separation.

`rollback_import(batch_02)` then restores `cards.back` from `card_before_json` and leaves the card row in place (it predates the batch). This is the path the original draft could not support at all — no gap found now, but only because §1.10 was patched in the previous round to add `card_before_json`; this walkthrough is what confirms the patch actually closes the loop rather than just looking plausible on paper.

## 4. Building a mix and generating a session

The learner also manually adds `crd_bayt` into `col_verbs` (wanting "house" reviewed alongside verbs):

`add_membership(crd_bayt, col_verbs, level_id: NULL) -> mem_004`

Current membership table:

| id | card_id | collection_id |
|---|---|---|
| mem_001 | crd_bayt | col_basics |
| mem_002 | crd_maa | col_basics |
| mem_003 | crd_kataba | col_verbs |
| mem_004 | crd_bayt | col_verbs |

The learner selects both collections and presses Mix. The filter is the shallow shape §1.7 says Milestone One's builder produces:

```json
{"node": "any", "children": [
  {"node": "source", "type": "collection", "id": "col_basics"},
  {"node": "source", "type": "collection", "id": "col_verbs"}
]}
```

`evaluate_view` walks each source: `col_basics` matches `{crd_bayt, crd_maa}` (2 memberships), `col_verbs` matches `{crd_kataba, crd_bayt}` (2 memberships) — **4 raw matches, 3 distinct cards** (`crd_bayt` appears via both). Unioning to a set, as §1.7/§2.4 currently specify, gets you the 3 distinct ids but silently throws away the fact that there were 4 matches, and `generate_session`'s `duplicates_collapsed` count (spec §7's preview requirement, §4.3's interstitial) has nothing left to compute from. **This is a real gap** — closed below, not deferred, because it's a data-flow bug rather than a policy question: `evaluate_view` must return per-card match counts (or the resolving code must count matches before deduplicating), not a bare set. See §7.A.1.

With that fixed, `generate_session(selection: <above>, policy: 'equal-source', seed: 42)` proceeds:

1. Resolve: `{crd_bayt: 2 matches, crd_maa: 1, crd_kataba: 1}`, `duplicates_collapsed = 4 - 3 = 1`.
2. Apply `equal-source`: give each *selected source* equal representation. But `crd_bayt` was matched by both sources — which source does it count against? Attributing it to both would double-count it against the equal-representation target; attributing it to only one (first-selected? most-specific? random?) is arbitrary and unspecified anywhere in the product spec or this design. **This is not a bug to patch — it's a genuine open question about what "equal-source" means when sources overlap**, and it is exactly the kind of thing the mixing-policy document needs to define precisely (source attribution rule) rather than something this walkthrough should invent an answer to. See §7.B.1.
3. Direction: nothing in `generate_session`'s signature (`selection, policy, seed?, size_limit?`) or in `sessions`/`session_queue` says whether `crd_bayt` is queued `front_to_back`, `back_to_front`, or both. `session_queue.direction` is `NOT NULL`, so *something* has to decide it before the row can be written — the schema requires an answer the operation signature doesn't provide a way to give. **Confirmed gap**, deferred per the user's own framing of the next document ("direction selection" was named explicitly). See §7.B.2.
4. Mode: `sessions` has no column recording whether this session is typed or self-graded recall. The study screen (§4.4) dispatches on "the mode(s) configured for that session," but nothing configures it anywhere in the schema. Unlike direction (a policy question) and source attribution (a policy question), this is simply a missing column with an obvious fix — not a mixing algorithm at all, just session configuration. **Fixed now.** See §7.A.2.

For this walkthrough to proceed at all, two placeholder decisions are made *only for the sake of tracing the rest of the system*, not as a design ruling: `crd_bayt` is attributed to `col_basics` for equal-source purposes (arbitrary — first source in selection order), and all three cards are queued `front_to_back` only. Both are flagged, not settled, by that placeholder status.

Resulting `sessions` row (after the §7.A.2 fix adds `study_mode`):

| id | selection_json | mixing_policy | seed | card_count | duplicates_collapsed | study_mode |
|---|---|---|---|---|---|---|
| ses_01 | (frozen 3-card snapshot) | equal-source | 42 | 3 | 1 | self_graded |

`session_queue`: three rows, `(ses_01, 0, crd_bayt, front_to_back)`, `(ses_01, 1, crd_kataba, front_to_back)`, `(ses_01, 2, crd_maa, front_to_back)` — order itself is a policy output that also isn't specified precisely yet (equal-source says representation, not interleaving order — another item for §7.B).

## 5. Submitting the first review

The learner studies `crd_bayt` front-to-back, self-graded, and grades it `Good`.

`submit_review(session_id: ses_01, card_id: crd_bayt, direction: 'front_to_back', grade: 'Good')`:

1. Look up `card_review_state(crd_bayt, front_to_back)` — no row exists (§1 starting state). Per §3's rule for a missing row, the scheduler named in `settings.default_scheduler_version` (say `fsrs-4.5`) is resolved from the `SchedulerRegistry`, and `initial_state()` is used as `state_before` rather than the lookup failing. **Confirmed working** — this is the one place this walkthrough set out to specifically test, since it's where the schema (`card_review_state` allows no row) and the scheduler boundary (a `Scheduler` trait method presupposing *a* state) have to meet, and they do.
2. `next_state(state_before, Good, reviewed_at)` returns a `SchedulerState` with a computed `due_at`, `stability`, `difficulty`, `interval_days`, `success_count: 1`.
3. Write `card_review_state(crd_bayt, front_to_back)` = that result, `scheduler_version = 'fsrs-4.5'`.
4. Insert `review_events`: `card_id: crd_bayt`, `direction: front_to_back`, `session_id: ses_01`, `prompt_shown: بيت`, `grade: Good`, `state_before_json` (the `initial_state()` output), `state_after_json` (step 2's output), all in the same transaction as step 3.

Because `crd_bayt` is also a member of `col_verbs`, reopening `col_verbs`'s level view immediately shows it as "learning" rather than "unseen" — the level-progress computation (§4.1) reads `card_review_state` joined through *any* membership, not a per-collection copy, so spec §9's "studying a card through one collection updates that card everywhere" holds without extra code. **No gap found.**

## 6. Ending the session and exporting

`end_session(ses_01)` sets `completed_at`. The learner then runs `export_archive`.

Tracing what the archive needs to contain in order to satisfy its own stated purpose — "a documented JSON archive... that can reconstruct an equivalent database" (spec §11, echoed in spec §16's acceptance criteria) — surfaces a real bug, not a policy question:

`review_events.session_id` is `REFERENCES sessions(id) ON DELETE RESTRICT`, meaning every `review_events` row is only valid alongside a matching `sessions` row. The `export_archive` operation as originally specified lists "cards, memberships, levels, collections, views, card_review_state, review_events, settings, schema_version" — **no `sessions` or `session_queue`**. Reconstructing a database from that archive would try to insert `ses_01`'s `review_events` row with `session_id = ses_01` and no `sessions` row to satisfy the foreign key; the restore fails, or (worse, if foreign keys are off during bulk load) silently produces a database that fails its first integrity check. The archive also omits `card_external_ids`, so a restored database that re-imports the same CSV a second time would reclassify everything as `new` instead of `update_match`, silently duplicating cards.

**This is fixed now**, not deferred — it's a straightforward completeness omission with one correct answer (include the referenced tables), not a design tradeoff. See §7.A.3.

With the fix, the archive for this scenario includes: 3 `cards` rows, 4 `memberships` rows, 1 `card_external_ids` row, 1 `card_review_state` row, 1 `review_events` row, 1 `sessions` row, 3 `session_queue` rows, 2 `import_batches` rows (batch_01, batch_02) with their `import_rows`, and `settings`/`schema_version`. `export_selection_csv` over just `col_basics` would separately produce a 2-row CSV (`crd_bayt`, `crd_maa`) with no scheduling columns, matching spec §11's plain-CSV path.

---

## 7. Findings

### A. Bugs — fixed now (technical design doc patched to match)

1. **`evaluate_view` / `duplicates_collapsed` data loss.** Deduplicating sources into a card-id set before counting throws away the information `generate_session` needs to report how many memberships collapsed. Fix: source resolution now returns `(CardId, match_count)` pairs; the set of keys is the eligible pool, `sum(match_count) - count(distinct cards)` is `duplicates_collapsed`.
2. **`sessions` had no `study_mode` column.** Nothing recorded whether a session was typed or self-graded recall, even though the study screen dispatches on it per session. Fix: added `study_mode TEXT NOT NULL CHECK (study_mode IN ('typed','self_graded'))` to `sessions`, and `generate_session` gained a required `study_mode` parameter.
3. **`export_archive` omitted `sessions`, `session_queue`, `card_external_ids`, `import_batches`, `import_rows`.** The first is a referential-integrity bug (`review_events.session_id` has nothing to point to on restore); the rest is a silent-data-loss bug (external-id matching breaks on re-import after restore). Fix: all five tables added to the archive's contents list.

### B. Open questions — deferred to the mixing-policy document

1. **Source attribution for overlapping cards.** When a card matches more than one selected source, `equal-source` and `proportional` need a defined rule for which source's quota it counts against (or how it's split/weighted across sources it matches) — not invented here.
2. **Direction selection.** Neither `generate_session`'s signature nor `sessions`/`session_queue` currently specify how front-to-back / back-to-front / alternating / both is chosen per card, even though `session_queue.direction` is `NOT NULL` and must be populated. This needs a `direction_policy` concept as a first-class part of the next document, not a silent default.
3. **Queue ordering within a policy.** `equal-source` (and the others) describe *representation*, not the resulting order cards appear in the queue — interleaved by source, blocked by source then shuffled, etc. is unspecified.
4. **Exhaustion behavior.** Undefined: what happens when `size_limit` exceeds the eligible pool, when a selected source is empty at generation time, or when `due-first` runs out of due cards before reaching the limit and has to decide whether/how to backfill with new cards.

None of the four items in (B) block Milestone One's schema or domain-operation surface — the walkthrough only needed a placeholder answer to keep tracing, not a real one — but all four block writing the mixing-policy document itself, since each is a precise algorithmic decision that document is supposed to make.
