# Manual Evaluation Follow-up Plan

## Purpose

This file tracks the remaining manual evaluation work after the five-recording Quality Engine v2 baseline setup.

The current PR establishes the baseline evidence pack. The manual evaluation pass will complete the deeper human-quality scoring needed before measuring Quality Engine v2 improvements.

## Follow-up checklist

### 1. Fill manually corrected perfect notes

Status: Not complete yet.

Placeholder files already exist:

- perfect_notes/M01_perfect_notes.md
- perfect_notes/M02_perfect_notes.md
- perfect_notes/M03_perfect_notes.md
- perfect_notes/M04_perfect_notes.md
- perfect_notes/S01_client_weekly_sync_perfect_notes.md

Each perfect-notes file should eventually include:

- purpose
- executive summary
- decisions
- action items
- owners
- deadlines
- open questions
- risks
- key points
- evidence notes
- what current MeetIQ missed or got wrong

### 2. Fill manual section-by-section scores

Status: Not complete yet.

Scorecard file already exists:

- five_recording_quality_scorecard.md

Manual scoring should cover:

- purpose quality
- summary quality
- action recall
- decision recall
- owner accuracy
- deadline extraction
- open-question separation
- entity/domain accuracy
- hallucination risk
- structure
- usefulness
- overall score

### 3. Confirm exact transcript/source mapping

Status: Not complete yet.

Transcript reference file already exists:

- transcript_references.md

Before final human scoring, confirm exact transcript/audio/video source mapping for:

- M01
- M02
- M03
- M04
- S01_client_weekly_sync

## Recommendation

This PR is sufficient as the baseline setup PR.

The next evaluation pass should fill the perfect notes and manual scorecard before or during the Quality Engine v2 implementation work.

## Safety

This follow-up work is documentation and QA evaluation only.

It should not change:

- billing
- auth
- upload limits
- frontend UI
- backend processing
- deployment settings
- production environment configuration
