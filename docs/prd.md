# PRD: Meeting Notes Assistant MVP

## Overview
Automate meeting note-taking: ingest audio/video + slides, transcribe, summarize (decisions, actions, owners), push to Slack/Notion, and keep a searchable history.

## MVP Scope
- Upload/ingest recording (<2 hrs)
- Transcription (with diarization if provider supports)
- LLM summary to structured JSON
- Slides OCR (PDF/images)
- Integrations: Slack + Notion (basic)
- Searchable history (to be completed post-MVP with embeddings)
- Guardrails: consent banner, retention (30/90 days)

## Acceptance Criteria
- <10 min processing for a 1-hr meeting
- ≥90% explicit action items captured with owners
- Slides OCR searchable
- Slack/Notion push succeeds
