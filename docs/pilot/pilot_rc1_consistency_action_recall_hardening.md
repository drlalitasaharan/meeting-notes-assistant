# Pilot RC1 Consistency + Action Recall Hardening

## Goal

Move the Meeting Notes Assistant from approximately 83/100 to 90/100 by improving:

1. Consistency across different meeting types
2. Action item recall
3. Demo-safe output polish

This workstream should not expand product scope. It should harden the current product.

---

## 1. Two-pass action extraction

### Pass 1: Strict structured action extraction

Capture clear action items where the transcript has:

- owner
- action verb
- task
- optional due date

Example:

John will send the updated proposal by Friday.

Expected action:

{
  "owner": "John",
  "task": "Send the updated proposal",
  "due_date": "Friday",
  "status": "open",
  "priority": "medium",
  "confidence": 0.90
}

### Pass 2: Recall recovery from action-like language

Recover weaker but important action signals from phrases such as:

- will
- should
- need to
- follow up
- send
- prepare
- review
- confirm
- schedule
- finalize
- update
- share
- check
- make sure

Example:

We should follow up with the client next week.

Expected action:

{
  "owner": "Team",
  "task": "Follow up with the client",
  "due_date": "next week",
  "status": "open",
  "priority": "medium",
  "confidence": 0.72,
  "evidence": "We should follow up with the client next week."
}

---

## 2. Confidence bands

| Confidence | Behavior |
|---|---|
| 0.85+ | Show as confirmed action |
| 0.65-0.84 | Show if evidence-supported |
| 0.45-0.64 | Possible next step only |
| Below 0.45 | Suppress |

Rules:

- Do not show weak actions as confirmed actions.
- Do not create fake actions from general discussion.
- Suppress action candidates without a clear task.
- Preserve Meeting 86 non-meeting safety behavior.

---

## 3. Evidence anchoring

Every decision and action should internally retain a source/evidence sentence.

Evidence anchoring helps with:

- debugging
- hallucination prevention
- quality scoring
- regression testing
- future enterprise trust features

---

## 4. Deterministic cleanup

Suppress:

- agenda-only fragments
- vague strategy notes
- duplicated actions
- transcript leakage
- malformed markdown
- fake actions in non-meeting audio

Normalize:

- owner names
- due dates
- repeated task variants
- final next steps

---

## Acceptance criteria

This workstream is successful when:

- Action recall improves on 30-minute and action-heavy meetings
- Meeting 86 non-meeting safety remains intact
- No duplicate or vague action items are introduced
- Markdown remains clean and client-facing
- JSON output remains valid
- Overall pilot-readiness score moves toward 90/100
