# Pilot RC1 Quality Gate

## Purpose

This quality gate protects the Pilot RC1 workflow from silent regression before pilot demos, outreach, or future release changes.

It validates backend health, meeting creation, audio upload, job completion, AI notes generation, markdown export, and structured output quality.

## Pass Threshold

Pilot RC1 passes only if the quality gate score is at least 85/100.

## Scoring Model

| Check | Points |
|---|---:|
| Backend health endpoint returned ok | 10 |
| Meeting was created | 10 |
| Audio upload returned a processing job | 10 |
| Processing job succeeded | 20 |
| Summary was generated | 10 |
| Purpose and outcome slots were generated | 10 |
| Key points were generated | 10 |
| Decisions were generated | 10 |
| Action items were generated | 10 |
| Total | 100 |

## Local Run Command

./bin/dc up -d
bash scripts/pilot_rc1_quality_gate.sh

Optional environment variables:

- BASE_URL=http://127.0.0.1:8000
- THRESHOLD=85

## Output Files

The quality gate writes evidence to test_outputs/pilot_rc1_quality_gate/.

## Product Interpretation

A passing quality gate means the selected Pilot RC1 workflow is functioning end-to-end and producing minimum acceptable structured meeting intelligence output.

A passing result does not mean the product is fully broad-market ready. It means the controlled Pilot RC1 workflow is safe enough to preserve and repeat for demos, rehearsals, and pilot-readiness checks.
