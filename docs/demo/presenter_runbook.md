# Presenter runbook

## Before the demo

Run from the project root:

```bash
cd /Users/lalitasaharan/Code/AJENCEL/meeting-notes-assistant || exit 1
git checkout main
git pull origin main
./bin/dc up -d
curl -fsS http://localhost:8000/healthz | jq
```

## Confirm validated artifact exists

```bash
test -f test_outputs/demo_rehearsal/meeting_181_external_ready_notes_after_cleanup_fix.md && echo "Validated 10-minute artifact exists"
```

## Open validated markdown

```bash
sed -n "1,220p" test_outputs/demo_rehearsal/meeting_181_external_ready_notes_after_cleanup_fix.md
```

## Recommended demo order

1. Start with the problem.
2. Explain the product in one sentence.
3. Show upload flow.
4. Show generated notes.
5. Highlight Decisions and Action Items.
6. Mention validated 10-minute rehearsal.
7. Close with pilot next step.

## Presenter reminder

Do not overclaim.

Use this phrase:

> This is ready for a controlled external pilot/demo, not yet a broad production launch.

## Success criteria for the call

The demo is successful if the viewer understands:

- What problem the product solves
- What the workflow looks like
- What the generated output contains
- Why structured notes are more useful than a transcript
- What the next pilot step would be
