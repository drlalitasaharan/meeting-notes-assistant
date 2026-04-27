# Pilot RC1 Decision and Action Extraction Patch Results

## Purpose

This report validates the deterministic extraction patch and structured fallback for Pilot RC1 decision and action recall.

## Result

- Benchmark cases: 5
- Jobs succeeded: 5/5
- Average after-patch benchmark score: 100.0/100
- Cases with structured decisions: 5/5
- Cases with structured actions: 5/5
- Status: PASS

## Acceptance Criteria

- Target average score: at least 80/100
- Target decision recall: at least 4/5 cases
- Target action recall: at least 4/5 cases
- No job-completion regression

## CSV Summary

~~~csv
case,meeting_id,job_id,status,summary_len,key_points,decisions,actions,purpose_len,outcome_len,score
01_client_weekly_sync,247,2a1f9d71-3abb-4bde-a3a1-e64fde48b35a,succeeded,156,2,1,1,156,174,100
02_product_planning,248,d748dd7c-fcd0-4e59-814c-b46619dffaf9,succeeded,177,2,2,2,118,57,100
03_sales_discovery,249,54f4cbf1-ea98-4e70-8495-446d771a333e,succeeded,198,4,1,2,139,57,100
04_engineering_standup,250,d506ae3f-687b-4c0e-8039-a03960ea6ebe,succeeded,120,4,2,1,61,57,100
05_executive_decision_review,251,e57e79c0-3271-479f-b9ac-2d0493f7f16c,succeeded,210,5,4,2,151,57,100
~~~
