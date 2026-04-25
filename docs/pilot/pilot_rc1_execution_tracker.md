# Pilot RC1 execution tracker

Release: v0.1.0-pilot-rc1
Status: Ready for controlled pilot

## Goal

Run a controlled pilot using the frozen Pilot RC1 baseline.

The pilot should validate whether Meeting Notes Assistant is useful for short, structured business meetings before expanding to broader use cases.

## Recommended pilot scope

Use this release for:

- Short business meetings
- Structured client or internal syncs
- Meetings with clear decisions and action items
- Demo and pilot validation workflows

Avoid using this release as a broad claim for:

- Long unstructured recordings
- Noisy audio
- Multi-hour meetings
- Legal, medical, or high-risk compliance notes
- Fully automated client delivery without review

## Pilot success metrics

Track the following for each pilot meeting:

| Metric | Target |
|---|---|
| Processing completes successfully | Yes |
| Markdown output is readable | Yes |
| Summary is usable | Yes |
| Decisions are accurate enough for review | Yes |
| Action items are useful | Yes |
| Manual cleanup time is reduced | Yes |
| User would use it again | Yes / Maybe / No |

## Pilot meeting log

| Date | User / Team | Meeting type | Duration | Result | Notes |
|---|---|---:|---:|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

## Feedback categories

Use these categories when reviewing feedback:

1. Summary quality
2. Decision extraction
3. Action item extraction
4. Formatting and markdown quality
5. Upload and processing experience
6. Speed and reliability
7. User trust and review requirements
8. Missing features

## Go / no-go criteria for next release

Move toward the next release only if:

- At least 3 to 5 real pilot meetings complete successfully.
- Outputs are useful after light human review.
- No major trust or hallucination issue appears.
- The demo flow remains stable.
- CI and prodready smoke tests remain green.

## Known follow-up work

- Reduce Docker build context with `.dockerignore`.
- Improve build speed and image hygiene.
- Add more real-world pilot examples.
- Track quality by meeting type and duration.
- Keep Pilot RC1 as the frozen baseline.
