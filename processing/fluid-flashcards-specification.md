# Fluid Flashcards

## Product specification, version 0.1

Status: initial implementation specification  
Date: 21 August 2026

## 1. Purpose

Fluid Flashcards is a local-first flashcard organizer for large, long-lived personal collections. It preserves the immediate intelligibility of early Memrise while making cards easy to regroup, shuffle, combine, split, and reuse.

The product is designed for collections containing tens of thousands of cards across languages, technical glossaries, and other subjects. It assumes that organization will change over time. Reorganization must therefore be inexpensive and must never destroy learning history.

The governing invariant is:

> Cards own content and learning state. Collections only select cards.

A card is stored once. It may appear in any number of collections, levels, filtered views, and study sessions without being copied. Moving or removing a card from a collection does not erase the card or reset its history.

## 2. Design principles

The interface must make the common path obvious: choose material, press Study, answer, and continue. Scheduling terminology and advanced controls must remain outside this path.

Collections are composable views rather than exclusive folders. The learner must be able to select several collections, levels, tags, or search results and immediately mix them into one session.

Organization and scheduling are independent. Changing where a card appears must not alter when it is due. Changing a card's wording must not silently reset it.

Active recall takes priority over recognition. Multiple-choice study is supported, but answer choices must not reveal the correct answer through shared wording or definitions containing the answer.

The application must work without an account or network connection. The user's collection must remain exportable in documented, ordinary formats.

## 3. Terminology

A **card** is a persistent learning item with one stable identifier, one or more prompts, one or more accepted answers, metadata, and learning state.

A **collection** is a named, ordered selection of cards. A collection may represent a Memrise-style course, a subject, a temporary project, or any other grouping.

A **level** is an optional ordered subdivision displayed within a collection. Levels provide visible progression but do not own their cards.

A **tag** is an unordered label attached directly to a card.

A **view** is a dynamically evaluated selection defined by filters. For example, `Arabic + verbs + weak` is a view whose membership changes as cards change.

A **mix** is a temporary or saved combination of collections, levels, tags, views, or explicit card selections.

A **session** is a fixed study queue generated from a selection and a mixing policy. Once started, its membership is stable unless the learner explicitly regenerates it.

## 4. Intended user experience

The home screen shows the card library, collections, and a prominent Study action. Every collection displays its total cards, cards due, recent progress, and optional level sequence.

Selecting one source permits ordinary study. Selecting several sources reveals a Mix action. The learner can begin immediately with sensible defaults or adjust direction, order, size, and selection policy.

The card editor opens without leaving the current context. Creating several cards in succession requires no repeated navigation. Keyboard operation is supported throughout creation and study.

Progress is visually legible in the manner of Memrise's course levels: unseen, learning, familiar, and mastered cards are distinguishable at a glance. These states summarize the scheduler; they do not replace its underlying data.

## 5. Core entities

### 5.1 Card

Each card contains a UUID, creation and modification timestamps, status, prompts, answers, notes, tags, provenance, and optional media references.

A card may contain multiple named fields, but v0.1 presents two primary fields: `front` and `back`. The data model must allow later card types without migrating the basic entity.

Card status is one of `active`, `suspended`, or `archived`. Suspended cards remain organized but do not enter automatically scheduled sessions. Archived cards are hidden from ordinary views but remain recoverable.

Duplicate content is permitted only after an explicit warning. Duplicate identity is impossible because every card has a unique identifier.

### 5.2 Collection membership

Membership links a card to a collection and may assign it to a level and a position. Membership contains no scheduling state.

The same card may have several memberships. Deleting a membership removes only that relationship. Deleting the final membership leaves the card in the library unless the user explicitly archives or deletes the card.

### 5.3 Learning state

Learning state belongs to the pair `(card, direction)`. Studying Arabic to English and English to Arabic therefore produces related but distinct records.

Each record stores due time, stability or interval, difficulty, lapse count, successful review count, last result, last reviewed time, and review history. The exact scheduling algorithm is replaceable behind a stable interface.

### 5.4 Review event

Every submitted answer creates an append-only event containing the card identifier, direction, prompt shown, response when retained, grade, response time, session identifier, timestamp, and scheduler state before and after the review.

Editing organization never rewrites review events. Undo creates a compensating event or marks the immediately preceding event as void while preserving the audit trail.

## 6. Organization requirements

The learner can create, rename, reorder, duplicate structurally, archive, and delete collections. Structurally duplicating a collection copies its arrangement and memberships but not its cards.

Cards can be added to or removed from several collections in one operation. Dragging cards between collections defaults to adding membership; an explicit Move command adds the destination membership and removes the selected source membership.

Collections can be merged as either a saved mix or a new materialized collection. A saved mix retains references to its sources. A materialized collection receives memberships for the current result set. Neither operation duplicates cards.

Collections can be split by level, tag, search rule, selection, or fixed size. Splitting creates memberships or saved views and preserves the source unless the learner explicitly chooses to replace its arrangement.

All organizational changes except permanent deletion are undoable during the current session. Destructive operations require an exact preview of the affected cards, memberships, and review records.

## 7. Mixing and shuffling

A study selection may contain any combination of collections, levels, views, tags, search results, and individually selected cards.

The following mixing policies are required:

`full-shuffle` randomizes all eligible cards uniformly.

`proportional` samples from each source in proportion to its eligible population.

`equal-source` gives each selected source equal representation regardless of its size.

`interleave` alternates sources as evenly as possible.

`weakest-first` orders by the lowest estimated recall probability, with overdue status as a secondary factor.

`due-first` presents scheduled reviews before optional new or early-review cards.

When a card occurs in more than one selected source, it appears only once in the generated queue unless repetition is explicitly requested. The session preview reports how many duplicate memberships were collapsed.

The learner may supply a random seed so a shuffle can be reproduced. Replaying a previous session selection does not replay obsolete scheduling decisions unless an exact historical replay is explicitly requested.

## 8. Study modes

V0.1 supports typed recall, self-graded recall, and multiple choice. Each mode supports front-to-back, back-to-front, alternating, or both-directions scheduling.

Typed answers undergo Unicode normalization, configurable case handling, whitespace normalization, and optional diacritic tolerance. The original submitted response remains visible during grading.

Self-graded recall shows the answer after reveal and offers `Again`, `Hard`, `Good`, and `Easy`. Keyboard shortcuts must be visible until learned and configurable thereafter.

Multiple-choice distractors may be manually specified or drawn from an eligible pool. Automatic distractors must never include the correct answer, a normalized equivalent, or an option whose definition contains the answer as an obvious substring. The editor provides a preview of the actual question and choices.

No answer is committed before the learner submits it. Revealing an answer without grading does not count as a successful review.

## 9. Scheduling

V0.1 uses a conventional four-grade spaced-repetition scheduler with separate state per direction. The initial implementation may use an established open algorithm such as FSRS, provided its parameters and implementation version are recorded.

The interface exposes due cards, new cards, and optional early reviews without requiring the learner to understand the algorithm. Daily limits are optional and can be overridden for any session.

Studying a card through one collection updates that card everywhere. When the same card is encountered through another collection, the updated due state is immediately visible.

A manual `Reset learning state` operation is available for selected cards and directions. It is never implied by moving, importing, editing, tagging, merging, or splitting.

## 10. Search and selection

Search covers prompts, answers, notes, tags, collection names, levels, and provenance. Results update as the learner types.

Filters include collection membership, level, tag, status, direction, due state, mastery band, lapse count, creation date, modification date, and last review date. Filters can be combined with AND, OR, and NOT and saved as views.

Every result screen supports Select all, Select visible, invert selection, add membership, remove membership, tag, suspend, archive, export, and Study.

## 11. Import and export

V0.1 imports UTF-8 CSV and TSV with a field-mapping preview. It supports front, back, notes, tags, collection, level, manual distractors, and external identifier columns.

Imports are staged before commitment. The preview reports new cards, exact duplicates, probable duplicates, updates matched by external identifier, malformed rows, and missing required fields. The learner chooses the action for each category.

An import batch has its own identifier and can be rolled back without affecting later review history for pre-existing cards.

The application exports the complete collection as a documented JSON archive containing cards, memberships, views, learning states, review events, settings, and schema version. It also exports selected cards as ordinary CSV or TSV. Media are included in a portable archive by relative reference.

No proprietary format may be the sole export path.

## 12. Local-first persistence

The application stores its authoritative state locally in SQLite. Database writes occur transactionally. Foreign-key constraints are enabled, and schema migrations are versioned and reversible when feasible.

Automatic timestamped backups are created before migrations and destructive bulk operations. The user can choose a backup directory and restore from the interface.

The application does not require sign-in. Network synchronization is outside v0.1, but identifiers and event records must not preclude later multi-device synchronization.

## 13. Accessibility and interaction

All essential functions are operable by keyboard. Focus order is predictable, visible, and restored sensibly after dialogs close.

The study screen avoids unnecessary animation and layout movement. Text size and contrast satisfy WCAG 2.2 AA. Color is never the only indication of learning state.

Arabic and other right-to-left text are first-class. Direction may be detected per field and overridden per card. Unicode text must round-trip without transliteration or normalization loss.

## 14. Non-goals for version 0.1

V0.1 does not include public course hosting, a social feed, competitive leaderboards, advertising, mandatory gamification, automatic AI card generation, collaborative editing, or cloud synchronization.

It does not attempt to reproduce Memrise's later video content or commercial language courses. Its target is the earlier course-and-level workflow applied to user-controlled material.

It does not implement a general knowledge graph. Dependencies, forward and backward pointers, and admissibility-based repetition remain possible extensions after the basic card, collection, and review invariants are proven.

## 15. Suggested implementation boundary

The first implementation should be a responsive local web application backed by a small local service and SQLite. The interface should remain usable in an ordinary desktop browser and should not depend on a remote server.

The backend must expose domain operations rather than raw table mutation. Operations include `create_card`, `update_card`, `add_membership`, `remove_membership`, `create_view`, `generate_session`, `submit_review`, `stage_import`, `commit_import`, and `export_archive`.

Random queue generation must occur from an explicit selection snapshot and seed. Scheduler updates and review-event creation must occur in one transaction.

## 16. Acceptance criteria for version 0.1

The application is ready for personal use when it can import a 30,000-card UTF-8 collection without lost text or duplicate proliferation; display collections and Memrise-style ordered levels; combine at least ten arbitrary sources into one session; generate each required mixing policy; collapse cards selected through multiple memberships; study in both directions with independent state; preserve learning history through every organizational operation; recover from an interrupted import; export a complete archive that can reconstruct an equivalent database; and perform ordinary library, search, organization, and study actions without network access.

For a 30,000-card local collection on ordinary desktop hardware, common searches should visibly update within 100 milliseconds, opening a collection within 200 milliseconds, and generating a 1,000-card mixed queue within 500 milliseconds.

## 17. First implementation milestone

Milestone One contains the SQLite schema, CSV/TSV staged import, card library, collections and ordered levels, many-to-many membership, selection across several sources, full shuffle and equal-source mixing, typed and self-graded bidirectional study, review-event history, a basic scheduler, and full JSON export.

Milestone One intentionally omits automatic distractor generation, rich media, saved Boolean views, advanced mixing policies, and synchronization. Its purpose is to validate the central invariant under real imported material before expanding the system.

## 18. Open decisions

The implementation language and desktop packaging remain open. A Rust local service would fit the scale, portability, and explicit domain model; a TypeScript interface would permit rapid iteration. Packaging can be deferred until the browser-based local workflow is stable.

The visual metaphor remains open. The strongest current direction combines Memrise-style progression levels with compact swatch-like cards, but visual design must follow successful organization and study tests rather than determine the data model.

The scheduler should be selected during Milestone One by comparing a minimal FSRS implementation with a simpler interval scheduler. The selection criterion is transparent, stable behavior across imported history, not maximal configurability.
