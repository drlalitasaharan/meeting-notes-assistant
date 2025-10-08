# Meeting Notes Assistant

[![Release](https://img.shields.io/github/v/release/drlalitasaharan/meeting-notes-assistant)](https://github.com/drlalitasaharan/meeting-notes-assistant/releases)
[![CI](https://github.com/drlalitasaharan/meeting-notes-assistant/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/drlalitasaharan/meeting-notes-assistant/actions/workflows/ci.yml)
[![Lint](https://github.com/drlalitasaharan/meeting-notes-assistant/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/drlalitasaharan/meeting-notes-assistant/actions/workflows/lint.yml)

FastAPI + Streamlit app to create meetings, upload slides, run a processing pipeline (OCR/LLM), and produce notes.  
Local dev supports both **bare-metal** and **Docker**.

---

## Quick start (bare-metal)

```bash
make venv
cp .env.example .env
make run-api          # uvicorn backend
make run-frontend     # Streamlit UI

