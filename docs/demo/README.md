# Demo Readiness and Pilot Packaging

This folder contains the demo and pilot-readiness package for Meeting Notes Assistant.

## Goal

Make the product easy to demonstrate, test, explain, and hand off during early pilot conversations.

## Current product position

Meeting Notes Assistant converts meeting recordings into structured notes with:

- Summary
- Purpose
- Outcome
- Risks
- Next steps
- Key points
- Decisions
- Action items

## Current strongest supported claim

The product currently performs best on short, structured business meetings.

## Current safety position

Non-meeting or narrative audio should not produce fake decisions, action items, or next steps.

## Protected baselines

The current quality and safety gates are protected by automated regression tests:

- Meeting 81: real-meeting quality baseline
- Meeting 86: non-meeting / narrative safety baseline

## Demo package contents

- runbook.md
- pilot_package_checklist.md
- sample_input_output_pack.md
- demo_success_criteria.md
- troubleshooting.md
