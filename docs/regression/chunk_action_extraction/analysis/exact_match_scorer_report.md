# Chunk Action Exact-Match Scorer Report

| Case | Expected | Matched | Missing | Unexpected | Precision | Recall | F1 | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ES2006c | 2 | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 | PASS |
| IB4001 | 1 | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 | PASS |
| IN1016 | 3 | 3 | 0 | 0 | 1.00 | 1.00 | 1.00 | PASS |
| IS1000b | 2 | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 | PASS |
| L01_controlled_long_business_50min | 10 | 0 | 10 | 2 | 0.00 | 0.00 | 0.00 | FAIL |
| M01_controlled_29min | 6 | 1 | 5 | 0 | 1.00 | 0.17 | 0.29 | FAIL |
| M04_10min | 0 | 0 | 0 | 0 | 1.00 | 1.00 | 1.00 | PASS |
| M05_risks_open_questions | 2 | 0 | 2 | 0 | 0.00 | 0.00 | 0.00 | FAIL |
| S01 | 3 | 1 | 2 | 2 | 0.33 | 0.33 | 0.33 | FAIL |

## Details

### ES2006c

Status: **PASS**

Missing expected actions:
- None

Unexpected actual actions:
- None

### IB4001

Status: **PASS**

Missing expected actions:
- None

Unexpected actual actions:
- None

### IN1016

Status: **PASS**

Missing expected actions:
- None

Unexpected actual actions:
- None

### IS1000b

Status: **PASS**

Missing expected actions:
- None

Unexpected actual actions:
- None

### L01_controlled_long_business_50min

Status: **FAIL**

Missing expected actions:
- Circulate the approved pilot pricing table by 2026-06-18 17:00
- Complete the storage and access-control security review by 2026-06-22 12:00
- Confirm the first pilot customer participant list by 2026-06-24 12:00
- Confirm whether regional data storage is required
- Create the customer onboarding checklist
- Prepare the pilot support-response templates by 2026-06-23 17:00
- Review whether contractor accounts may join the pilot
- Run the twelve-recording regression suite and document failures by 2026-06-25 17:00
- Upload the final demonstration recording by 2026-06-19 15:00
- Verify recording deletion from storage after the retention test

Unexpected actual actions:
- The Working Recommendation Is This, Use The Approved Sample Recording And Retain One Processed Backup Meeting For Demonstration Continuity, Before Confirming Anything, We - Test that recommendation against the pilot objective and current evidence
- Unassigned - Use explicit confirmation language when the group reaches agreement and explicit rejection language when an option is not selected

### M01_controlled_29min

Status: **FAIL**

Missing expected actions:
- Add stage timing logs to the worker output
- Create the clean ten-minute audio test and run it through the product
- Keep one backup meeting processed and ready before any live demo
- Package the final demo commands into one short runbook
- Prepare the short live-demo recording

Unexpected actual actions:
- None

### M04_10min

Status: **PASS**

Missing expected actions:
- None

Unexpected actual actions:
- None

### M05_risks_open_questions

Status: **FAIL**

Missing expected actions:
- Obtain written pricing approval and circulate the approved pricing table to the team by 5pm on June 18th, 2026
- Send the completed security review summary covering storage access, administrator permissions, and deletion controls by noon on June 22nd, 2026

Unexpected actual actions:
- None

### S01

Status: **FAIL**

Missing expected actions:
- Finish the remaining storage and access control checks by noon on June 22nd, 2026
- Upload the final sample recording by 3pm on June 19th, 2026

Unexpected actual actions:
- Unassigned - Confirm score, pricing, the sample recording and the security review
- Unassigned - Create owns the pricing table, Jordan owns the sample recording, and I own the security checklist
