# Hosted payment smoke-test record

Date: 2026-06-16

## Purpose

Record the hosted smoke-test result after adding the pricing/payment funnel, hosted payment-link documentation, manual payment request environment variable, and meetings UI cleanup.

## Current hosted configuration

Frontend:
- Vercel frontend deployed from main.
- NEXT_PUBLIC_API_BASE_URL configured.
- NEXT_PUBLIC_MANUAL_PAYMENT_REQUEST_URL configured as /support.

Backend:
- Render backend health check passed.
- Database check passed.
- Redis check passed.
- Storage check passed.

## Smoke-test results

- /pricing opens successfully.
- Logged-out header shows Pricing, Login, and Create account.
- Logged-in header shows New Upload, Meetings, Usage, Pricing, Support, and Logout.
- Free trial card is visible.
- Paid access card is visible.
- PayPal button safely shows Payment link coming soon.
- Square button safely shows Payment link coming soon.
- Manual payment request button is active.
- Manual payment request opens /support.
- /support opens successfully.
- /login opens successfully.
- Login/backend connectivity is restored.
- /usage opens successfully after login.
- Usage dashboard shows free trial state.
- Usage dashboard shows View pricing upgrade card.
- View pricing opens /pricing.
- /meetings opens successfully.
- Visible newline artifact is no longer present on the meetings page.

## Intentionally not configured yet

- PayPal checkout/payment link is not configured yet.
- Square checkout/payment link is not configured yet.
- PayPal live payment testing has not started.
- Square live payment testing has not started.
- Stripe checkout is still pending activation/final integration.

## Pass/fail summary

PASS:
- Backend health.
- Pricing page.
- Manual payment request path.
- Support page.
- Login page.
- Usage upgrade path.
- Meetings page after newline-artifact fix.

DEFERRED:
- PayPal sandbox payment test.
- Square sandbox payment test.
- Stripe final integration.

## Safety confirmation

Frontend payment links do not grant paid access directly. Paid access remains controlled by verified PayPal/Square webhook processing and billing subscription state.

## Next recommended step

Keep PayPal and Square links disabled until sandbox checkout links and webhook credentials are ready. Start with PayPal sandbox payment testing before adding live payment links.
