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
01_client_weekly_sync,212,1222cf0c-7bd1-4b31-87ce-bcc1f1af858f,succeeded,156,2,2,1,156,174,100
02_product_planning,213,eb6c881c-fd22-40bf-adec-f4bff6bb2b58,succeeded,177,2,2,2,118,57,100
03_sales_discovery,214,d377f30a-7dda-42f4-820c-d850da7bdf25,succeeded,198,4,1,2,139,57,100
04_engineering_standup,215,a7e53f81-b29d-4246-8666-dbae90bb2f7c,succeeded,120,4,4,1,61,57,100
05_executive_decision_review,216,c4fe18f3-86c0-4f00-99d7-849bf055cde4,succeeded,210,5,5,3,151,57,100
~~~
