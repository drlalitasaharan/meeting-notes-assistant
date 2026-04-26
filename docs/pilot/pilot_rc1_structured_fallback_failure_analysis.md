# Pilot RC1 Structured Fallback Failure Analysis

## Current Status

The Pilot RC1 structured fallback benchmark completed without job failures, but did not improve structured decision/action recall.

## Observed Result

- Jobs succeeded: 5/5
- Average score: 61.0/100
- Structured decision cases: 0/5
- Structured action cases: 0/5
- Status: FAIL

## Interpretation

This is now an extraction-path issue, not an infrastructure issue.

Most likely causes to inspect next:

1. The structured fallback function exists but is not being called in the active notes generation path.
2. The fallback is being called but writes to fields that are not persisted or serialized.
3. The fallback is receiving sentence/input data that does not contain the decision/action trigger text.
4. The benchmark runner is counting different output fields than the patch writes.
5. The final result object is immutable or overwritten after fallback execution.

## Next Engineering Move

Patch only after confirming which cause is true. Do not commit the failed patch as a successful quality improvement.
