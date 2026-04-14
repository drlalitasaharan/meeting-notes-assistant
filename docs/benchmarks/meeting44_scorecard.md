# Meeting Notes Quality Scorecard

## Benchmark info
- Date: 2026-04-12
- Meeting ID: 44
- Audio / test file: demo_media/meeting_30min_script.wav
- Model version: local-summary-v3
- Branch / commit: feat/notes-v3-decisions-actions-summary
- Notes: Best current structured output before later recall regression

---

## Overall score

| Category | Max | Score |
|---|---:|---:|
| Purpose / Outcome / Summary | 20 | 17 |
| Decisions | 20 | 17 |
| Action Items | 25 | 17 |
| Key Points | 15 | 11 |
| Risks | 10 | 8 |
| Language / Polish | 10 | 10 |
| **Total** | **100** | **80** |

---

## 1) Purpose / Outcome / Summary — 17/20

### Purpose — 9/10
Checklist:
- [x] Clearly explains why the meeting happened
- [x] Not actually an action item
- [x] Not actually a decision
- [x] Not a status/result sentence
- [x] Business-readable

Notes:
Purpose is strong and stable:
“Review progress, confirm the next demo path, and align on pilot outreach and open risks.”
This is one of the clearest purpose lines across all test runs.

### Outcome — 4/5
Checklist:
- [x] Clearly states what came out of the meeting
- [x] Reflects the most important decisions or changes
- [x] Not vague or repetitive

Notes:
Outcome is concise and useful:
“The meeting resulted in decisions on the first pilot audience and the primary backup demo example.”
It is good, but still narrower than the cleaned ChatGPT reference.

### Summary — 4/5
Checklist:
- [x] Reads like an executive recap
- [x] Does not start with a random fragment
- [x] Consistent with purpose + outcome

Notes:
Summary is clean and business-readable. It is shorter and less rich than the reference, but structurally strong.

---

## 2) Decisions — 17/20

### Recall — 8/10
Checklist:
- [x] Captures the major decisions
- [ ] No obviously missing high-value decisions

Expected decisions for this benchmark:
- [x] First pilot audience = consultants / agencies / startup teams
- [x] Meeting 17 = primary backup demo example
- [ ] Ten-minute file = main proof of quality
- [ ] Thirty-minute file = stress test, not default live demo
- [ ] Practical positioning message, not broad platform pitch

Notes:
The two most important decisions are present, but the broader explicit decision set from the cleaned reference is still missing.

### Wording — 9/10
Checklist:
- [x] Clean and final wording
- [x] No speculative language
- [x] Not phrased like an action item

Notes:
Decision wording is clean and strong:
- The first pilot audience will be consultants, agencies, and small startup teams.
- Meeting 17 will be the primary backup demo example for the live client presentation.

---

## 3) Action Items — 17/25

### Recall — 7/10
Checklist:
- [x] Important actions are present
- [ ] No obviously missing high-value actions

Expected actions for this benchmark:
- [x] Team backup meeting before live demo
- [x] Lalita short live demo file
- [ ] Lalita clean ten-minute audio test
- [ ] Landing page / pilot outreach review
- [ ] Stage timing logs
- [x] Keep cleanup logic / defer deeper tuning
- [ ] Command checklist / runbook
- [ ] Save strongest output as primary demo artifact

Notes:
Three strong actions are present, but several useful follow-up items from the cleaned reference are still missing.

### Owners — 5/5
Checklist:
- [x] Owners are correct
- [x] No `Speaker`
- [x] No `Unassigned`

Notes:
This is a strong area in meeting 44.

### Task wording — 4/5
Checklist:
- [x] Task statements are imperative and clear
- [x] No narrative fragments
- [x] Decisions are not mixed into actions

Notes:
Action wording is mostly clean. The Team backup item could still be normalized slightly better:
“before any live demo” → “before the live demo”

### Due dates — 1/5
Checklist:
- [ ] Real due dates only
- [x] No broken values like `before the`
- [x] Blank is acceptable when uncertain

Notes:
No broken due dates remain, which is good, but there are also no useful due dates preserved here.

---

## 4) Key Points — 11/15

### Breadth — 7/10
Checklist:
- [x] Product status
- [ ] Demo plan / flow
- [x] Pilot audience / positioning
- [x] Technical risks
- [x] Quality / cleanup priorities

Notes:
Covers several important themes, but still misses some breadth from the cleaned reference, especially around landing page messaging, timing logs, and detailed live demo flow.

### Relevance — 4/5
Checklist:
- [x] No fluff
- [x] No near-duplicates
- [x] Not too narrow

Notes:
Key points are relevant and fairly clean, but they still feel narrower than the best human-edited version.

---

## 5) Risks — 8/10

### Recall — 4/5
Checklist:
- [x] Raw media path / sequencing risk
- [ ] Runtime risk on longer files

Notes:
The raw media path / sequencing risk is captured clearly.
The runtime-on-long-files risk is still missing.

### Precision — 4/5
Checklist:
- [x] Risks are real risks
- [x] No agenda/objective text here
- [x] No generic filler

Notes:
Risk precision is strong in this run.

---

## 6) Language / Polish — 10/10

### Readability — 5/5
Checklist:
- [x] Grammatically clean
- [x] Business-readable
- [x] Safe to show to a client

Notes:
This is the strongest user-facing markdown result so far.

### Cleanliness — 5/5
Checklist:
- [x] No transcript artifacts
- [x] No awkward owner/task phrasing
- [x] No broken normalization

Notes:
Very clean compared with earlier runs.

---

## Hard-fail checks

Fail the run if any of these are true:

- [ ] Purpose is actually an action item
- [ ] Purpose is actually a decision
- [ ] Decisions are empty when clear decisions exist
- [ ] `Speaker` appears in final action items
- [ ] `Unassigned` appears in final action items
- [ ] Broken due date appears
- [ ] Fake/meta action appears
- [ ] Agenda/objective text appears under risks

Notes:
No hard-fail issues in meeting 44.
This is why meeting 44 is the best current baseline.

---

## Reference comparison

### ChatGPT cleaned reference
How close is this run to the cleaned reference?

| Area | Reference stronger / equal / weaker | Notes |
|---|---|---|
| Summary quality | Reference stronger | Your summary is cleaner structurally, but less complete |
| Purpose clarity | Equal | Your explicit purpose field is actually a product advantage |
| Decision coverage | Reference stronger | You capture 2 major decisions; reference captures a fuller set |
| Action-item recall | Reference stronger | You capture 3 strong actions; reference captures many more |
| Key-point breadth | Reference stronger | Your key points are good, but still narrower |
| Risk capture | Reference stronger | You capture sequencing risk, but miss runtime risk |
| Language polish | Equal | Your markdown is now very polished and product-ready |

---

## Final verdict

- Total score: 80/100
- Pass / Fail: Pass
- Best improvements:
  - Correct purpose
  - Concise outcome
  - Clean decisions
  - Structured action items
  - Strong markdown layout
- Biggest misses:
  - Missing some action-item recall
  - Missing broader decision recall
  - Missing runtime risk
  - Key points still narrower than the cleaned ChatGPT reference
- Recommended next patch:
  - Improve action-item recall carefully without reintroducing fake/meta actions
