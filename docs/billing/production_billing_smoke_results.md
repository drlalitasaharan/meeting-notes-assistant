# Production Billing Smoke Results

## Status

Production billing smoke testing is complete for the primary Starter paid plan.

## Environment

- Frontend: Vercel production
- Backend: Render production
- Database: Render Postgres
- Queue/cache: Render Redis
- Storage: AWS S3
- Payment providers:
  - PayPal live
  - Square production

## PayPal Starter live test

Status: PASS

Confirmed:

- PayPal live checkout opened successfully.
- Starter payment completed successfully.
- MeetIQ payment success page confirmed paid access.
- Usage dashboard showed:
  - Plan: Starter
  - Billing provider: PayPal
  - Meetings used: 0 of 20
  - Remaining uploads: 20

Operational note:

- Refund attempt required sufficient PayPal balance or linked funding source.
- PayPal payout/refund operations should remain on the business operations checklist.

## Square Starter live test

Status: PASS

Confirmed:

- Square production checkout opened successfully.
- Checkout product: MeetIQ Starter
- Amount: US$23.00
- Currency: USD
- Square production API log showed:
  - Endpoint: POST /v2/online-checkout/payment-links
  - Status: 200
- Square payment completed successfully.
- Square webhook delivered successfully:
  - Event type: payment.updated
  - Webhook response: 200
- Usage dashboard showed:
  - Plan: Starter
  - Billing provider: Square
  - Meetings used: 0 of 20
  - Remaining uploads: 20

Important fix deployed:

- Commit `3ca9d4f1` fixed Square production environment mapping.
- Commit `dc4a0b2f` fixed Square webhook account email matching.
- The already-paid Square test account required one manual historical correction because the webhook was processed before the email-matching fix was deployed.
- Future Square payments should activate automatically from the MeetIQ account email stored in `payment.note`.

## Remaining optional tests

Not required before controlled launch:

- Square Pro Pilot $49 live payment test
- PayPal Pro Pilot $49 live payment test

These can be tested later if Pro Pilot becomes a primary public plan.

## Current billing readiness

- PayPal Starter: PASS
- Square Starter: PASS
- Manual payment request path: available
- Paid monthly upload limit: active
- Usage dashboard: active
- Production health checks: PASS

## Recommendation

Freeze payment-provider code unless a real production issue appears.

Next launch-readiness task:

Run paid-account upload smoke test:

1. Login as a paid Starter account.
2. Confirm Usage shows Starter / provider / 0 of 20.
3. Upload a short meeting.
4. Confirm processing completes.
5. Open generated notes.
6. Download Markdown.
7. Return to Usage.
8. Confirm usage increments to 1 of 20.
