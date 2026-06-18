# MeetIQ Commercial Billing Smoke Checklist

This checklist verifies the MeetIQ commercial billing flow after deployment.

Use this checklist after changes to billing, pricing, usage, admin billing visibility, support copy, PayPal checkout, or deployment configuration.

## Current known-good status

- PayPal checkout: complete
- PayPal capture: complete
- Billing success page: complete
- Usage paid-access display: complete
- Pricing payment-confirmation copy: complete
- Admin billing visibility: complete
- Admin email allowlist: complete
- Billing support, refund, and cancel policy copy: complete

## Required access

- GitHub repo
- Vercel frontend
- Render backend web service
- Render backend environment variables
- PayPal Sandbox or payment test account
- MeetIQ admin account listed in `ADMIN_EMAILS`

## Environment variables to confirm

Backend Render web service:

- `ADMIN_EMAILS`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`
- `PAYPAL_BASE_URL`
- `PAYPAL_WEBHOOK_ID`
- `DATABASE_URL`
- `REDIS_URL`
- S3/storage variables

Frontend Vercel:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SQUARE_CHECKOUT_URL`, if configured
- `NEXT_PUBLIC_MANUAL_PAYMENT_REQUEST_URL`, if configured

## 1. GitHub and deployment checks

Run from local repo:

```bash
cd /Users/lalitasaharan/Code/AJENCEL/meeting-notes-assistant || exit 1
source .venv/bin/activate

gh run list --branch main --limit 8
curl -s https://meeting-notes-assistant.onrender.com/healthz | python -m json.tool
git log --oneline --decorate -n 5
git status --short
```

Expected:

- Latest main checks pass
- Backend health returns `status: ok`
- DB, Redis, and storage are all `ok`
- Local repo is clean

## 2. Public pricing page check

Open:

```text
https://meetiq-frontend.vercel.app/pricing
```

Confirm:

- Free trial card is visible
- Paid access card is visible
- PayPal checkout button is visible
- Square checkout is marked as coming soon if not configured
- Manual invoice/payment request option is visible if configured
- Payment activation note says PayPal activates paid access after payment confirmation
- Old webhook-only payment wording is not present

## 3. Signup/login smoke check

Create or use a clean normal user account.

Confirm:

- Signup works
- Login works
- User lands on `/upload`, `/meetings`, or `/usage`
- Normal free-trial usage shows 0 of 1 used before upload

## 4. PayPal checkout smoke check

From the pricing page while logged in:

1. Click `Pay with PayPal`
2. Confirm MeetIQ opens PayPal checkout
3. Complete sandbox payment
4. Return to MeetIQ

Expected:

- PayPal opens correctly
- Payment can be completed
- User returns to `/billing/success`
- Success page confirms payment

## 5. Billing success page check

Expected success page:

- Shows `Payment confirmed`
- Shows plan `paid_pro`
- Shows status `active`
- Shows provider `Paypal`
- Shows `Check usage`
- Shows `Go to meetings`
- Shows billing support guidance

## 6. Usage dashboard paid-access check

Open:

```text
https://meetiq-frontend.vercel.app/usage
```

Expected for paid user:

- Shows `Paid access`
- Shows access status `Active`
- Shows provider `Paypal`
- Does not show trial-only guidance
- Shows paid-user guidance

## 7. Admin billing visibility check

Log in as an account listed in backend `ADMIN_EMAILS`.

Open:

```text
https://meetiq-frontend.vercel.app/admin
```

Expected:

- Admin page loads
- Billing operations section is visible
- Active paid users is visible
- Payment attempts is visible
- Failed attempts is visible
- Recent subscriptions are visible
- Recent payment attempts are visible

Also verify a non-admin user cannot access `/admin`.

Expected for non-admin:

```text
Admin access required
```

## 8. Support and billing policy copy check

Open:

```text
https://meetiq-frontend.vercel.app/support
```

Confirm:

- Billing support card is visible
- Billing, cancellation, and refund questions section is visible
- Copy says billing changes are handled manually during early access
- Copy says refund and cancellation requests are reviewed manually
- Copy tells users not to send payment card, bank, or password details

Open:

```text
https://meetiq-frontend.vercel.app/billing/cancel
```

Confirm:

- Checkout canceled message is visible
- Billing support button is visible
- Copy tells users to contact support for billing/manual payment questions

## 9. Render log check

In Render backend web service logs, confirm:

- Pre-deploy migration completed successfully
- App starts successfully
- No new billing endpoint errors
- No `billing_events` missing-table errors
- No admin billing endpoint 500 errors

Expected migration line:

```text
MeetIQ pre-deploy migration completed successfully
```

## 10. Final pass criteria

Mark the smoke test as PASS only if all are true:

- GitHub main checks pass
- Backend health is ok
- Pricing page copy is correct
- PayPal checkout opens
- PayPal payment completes
- Billing success page confirms paid access
- Usage dashboard shows paid access
- Admin dashboard shows billing operations
- Non-admin users are blocked from admin
- Support/refund/cancel copy is visible
- No backend health or billing errors are visible

## Known acceptable limitations

- Square checkout may be marked as coming soon
- Refund and cancellation requests are handled manually
- Full self-serve billing portal is not yet available
- Admin may show multiple active subscriptions for the same test user after repeated PayPal sandbox tests

## Suggested next hardening tasks

- Clarify paid plan limits and fair-use copy
- Add billing receipt/invoice copy
- Add Square checkout backup path
- Improve admin billing deduplication for repeated sandbox tests
- Add self-serve billing portal later
