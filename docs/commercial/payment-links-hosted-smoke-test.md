# Hosted payment links and pricing smoke test

This document describes the hosted payment-link configuration and smoke test checklist for the MeetIQ temporary commercial payment workflow.

## Purpose

MeetIQ now has:
- Billing foundation
- PayPal webhook activation
- Square webhook activation
- Pricing/payment funnel UI

This checklist keeps payment configuration safe by storing real payment links and provider secrets only in hosted environment variables, never in Git.

## Important safety rule

Do not commit real payment URLs, client secrets, webhook IDs, webhook signature keys, or provider credentials to the repository.

Frontend payment buttons may send users to payment providers, but frontend clicks must never grant paid access directly.

Paid access is activated only after verified PayPal or Square webhook events are processed by the backend.

## Vercel frontend environment variables

Set these in Vercel for the frontend deployment:

NEXT_PUBLIC_PAYPAL_CHECKOUT_URL=
NEXT_PUBLIC_SQUARE_CHECKOUT_URL=
NEXT_PUBLIC_MANUAL_PAYMENT_REQUEST_URL=

Expected behavior:
- If NEXT_PUBLIC_PAYPAL_CHECKOUT_URL is configured, the PayPal button opens that URL.
- If NEXT_PUBLIC_SQUARE_CHECKOUT_URL is configured, the Square button opens that URL.
- If NEXT_PUBLIC_MANUAL_PAYMENT_REQUEST_URL is configured, the manual payment button opens that URL.
- If any URL is not configured, the page shows Payment link coming soon.

## Render backend environment variables for PayPal

Set these in the Render backend API service, not in the frontend:

PAYPAL_ENV=sandbox-or-live
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_WEBHOOK_ID=

PayPal webhook endpoint:
POST /v1/billing/paypal/webhook

## Render backend environment variables for Square

Set these in the Render backend API service, not in the frontend:

SQUARE_WEBHOOK_SIGNATURE_KEY=
SQUARE_WEBHOOK_NOTIFICATION_URL=

Square webhook endpoint:
POST /v1/billing/square/webhook

## Hosted smoke test before real payment links

Use this first when no real payment links are configured:

1. Deploy frontend from main.
2. Open /pricing.
3. Confirm Free trial card is visible.
4. Confirm Paid access card is visible.
5. Confirm PayPal, Square, and manual payment options are visible.
6. Confirm missing links show Payment link coming soon.
7. Open /usage while signed in.
8. Confirm the Usage dashboard shows a View pricing upgrade card.
9. Confirm Header includes Pricing for logged-in users.
10. Confirm Header includes Pricing for logged-out users.

## Hosted smoke test after real payment links

Use this after payment URLs are configured in Vercel:

1. Redeploy frontend after setting Vercel environment variables.
2. Open /pricing.
3. Click PayPal and confirm it opens the expected PayPal checkout/payment URL.
4. Click Square and confirm it opens the expected Square checkout/payment URL.
5. Click manual payment request and confirm it opens the expected request form or contact flow.
6. Do not mark a user paid from the frontend.
7. Confirm paid access changes only after a PayPal or Square webhook event is received.

## Production readiness checklist

- Vercel frontend env vars configured.
- Render backend PayPal env vars configured.
- Render backend Square env vars configured.
- PayPal webhook URL points to the hosted backend.
- Square webhook URL points to the hosted backend.
- /pricing renders successfully.
- /usage links to /pricing.
- Payment buttons do not grant access directly.
- billing_events records provider webhook events.
- billing_subscriptions controls paid_pro access.

## Rollback

If a payment link is incorrect, remove or update the corresponding Vercel environment variable and redeploy the frontend.

If a webhook credential is incorrect, update the corresponding Render backend environment variable and redeploy/restart the backend service.
