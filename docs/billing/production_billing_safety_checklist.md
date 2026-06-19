# Production Billing Safety Checklist

## Current commercial billing status

### PayPal

- [x] PayPal implementation complete
- [x] PayPal live environment configured
- [x] PayPal Live Starter real payment test passed
- [x] MeetIQ activation confirmed: Starter / PayPal / 20 uploads
- [ ] PayPal test payment refund completed, or decision recorded to keep payment
- [ ] Business bank linked for future refunds/payouts, if needed

### Square

- [x] Square implementation complete
- [x] Square sandbox Starter test passed
- [x] Square sandbox Pro Pilot test passed
- [x] Square sandbox webhook activation passed
- [ ] Square production credentials configured
- [ ] Square production webhook configured
- [ ] Square production Starter real payment test passed
- [ ] Square production Pro Pilot real payment test passed, optional

---

## Required production environment variables

### PayPal production

Render backend must use:

    PAYPAL_ENV=live
    PAYPAL_CLIENT_ID=<PayPal Live Client ID>
    PAYPAL_CLIENT_SECRET=<PayPal Live Secret>
    PAYPAL_WEBHOOK_ID=<PayPal Live Webhook ID>
    PAYPAL_WEBHOOK_VERIFY_DISABLED=false
    MEETIQ_FRONTEND_BASE_URL=https://meetiq-frontend.vercel.app

Required PayPal webhook events:

- PAYMENT.CAPTURE.COMPLETED
- CHECKOUT.ORDER.COMPLETED
- PAYMENT.CAPTURE.REFUNDED
- CUSTOMER.DISPUTE.CREATED

### Square production

Render backend must use:

    SQUARE_ENV=production
    SQUARE_ACCESS_TOKEN=<Square Production Access Token>
    SQUARE_LOCATION_ID=<Square Production Location ID>
    SQUARE_WEBHOOK_SIGNATURE_KEY=<Square Production Webhook Signature Key>
    SQUARE_WEBHOOK_NOTIFICATION_URL=https://meeting-notes-assistant.onrender.com/v1/billing/square/webhook
    MEETIQ_FRONTEND_BASE_URL=https://meetiq-frontend.vercel.app

Required Square webhook event:

- payment.updated

Optional Square monitoring events:

- refund.created
- refund.updated

---

## Safety rules

- [ ] Do not mix sandbox credentials with production credentials.
- [ ] Do not use a sandbox webhook ID/signature key in production.
- [ ] Do not use a production Square access token with SQUARE_ENV=sandbox.
- [ ] Do not use a sandbox PayPal client ID/secret with PAYPAL_ENV=live.
- [ ] Do not run live payment tests using the same PayPal seller account as the buyer.
- [ ] Use fresh MeetIQ test accounts for each live payment test.
- [ ] Record payment provider, amount, plan, status, fee, net amount, and refund decision.
- [ ] Confirm usage dashboard after every payment test.
- [ ] Confirm webhook delivery after every payment test.
- [ ] Keep provider credentials secret and never commit them.

---

## Live payment smoke tests

### PayPal Starter

- [x] Create fresh MeetIQ user
- [x] Pay Starter $23 through PayPal live checkout
- [x] Return to MeetIQ success page
- [x] Usage shows Starter / PayPal / 20
- [ ] Refund completed, or decision recorded not to refund

### PayPal Pro Pilot

- [ ] Create fresh MeetIQ user
- [ ] Pay Pro Pilot $49 through PayPal live checkout
- [ ] Return to MeetIQ success page
- [ ] Usage shows Pro Pilot / PayPal / 100
- [ ] Refund completed, or decision recorded not to refund

### Square Starter

- [ ] Create fresh MeetIQ user
- [ ] Pay Starter $23 through Square production checkout
- [ ] Return to MeetIQ success page
- [ ] Usage shows Starter / Square / 20
- [ ] Refund completed, or decision recorded not to refund

### Square Pro Pilot

- [ ] Create fresh MeetIQ user
- [ ] Pay Pro Pilot $49 through Square production checkout
- [ ] Return to MeetIQ success page
- [ ] Usage shows Pro Pilot / Square / 100
- [ ] Refund completed, or decision recorded not to refund

---

## Rollback plan

### PayPal rollback

If live PayPal has issues, restore sandbox PayPal env vars:

    PAYPAL_ENV=sandbox
    PAYPAL_CLIENT_ID=<PayPal Sandbox Client ID>
    PAYPAL_CLIENT_SECRET=<PayPal Sandbox Secret>
    PAYPAL_WEBHOOK_ID=<PayPal Sandbox Webhook ID>
    PAYPAL_WEBHOOK_VERIFY_DISABLED=false

Then redeploy backend.

### Square rollback

If live Square has issues, restore sandbox Square env vars:

    SQUARE_ENV=sandbox
    SQUARE_ACCESS_TOKEN=<Square Sandbox Access Token>
    SQUARE_LOCATION_ID=<Square Sandbox Location ID>
    SQUARE_WEBHOOK_SIGNATURE_KEY=<Square Sandbox Webhook Signature Key>
    SQUARE_WEBHOOK_NOTIFICATION_URL=https://meeting-notes-assistant.onrender.com/v1/billing/square/webhook

Then redeploy backend.

---

## Final production billing status

Only mark production billing ready when all required checks pass:

- [ ] PayPal Live Starter passes
- [ ] Square Production Starter passes
- [ ] Webhooks pass for both providers
- [ ] Usage dashboard updates correctly for both providers
- [ ] Refund/bank handling decision recorded
- [ ] Backend health is OK
- [ ] GitHub checks are green
- [ ] No sandbox credentials are active in public production checkout unless intentionally documented
