# PayPal static-link partial smoke-test

Date: 2026-06-17

## Purpose

Record the hosted PayPal sandbox smoke-test result after temporarily enabling a static PayPal checkout URL on the pricing page.

## Configuration tested

- Render backend PayPal sandbox variables were configured.
- PayPal sandbox webhook was configured for the MeetIQ backend webhook URL.
- Vercel frontend temporarily configured NEXT_PUBLIC_PAYPAL_CHECKOUT_URL.
- Pricing page displayed an active PayPal payment button.

## Result

PASS:
- Pricing page loaded successfully.
- PayPal button changed from Payment link coming soon to Pay with PayPal.
- PayPal sandbox checkout opened from the MeetIQ pricing page.
- Sandbox payment page displayed MeetIQ Early Access for 10 USD.
- Sandbox payment completed successfully.
- MeetIQ app remained usable after returning to the production domain.
- Static PayPal checkout URL was removed from Vercel after the test.
- Pricing page returned to the safe state with PayPal showing Payment link coming soon.

NOT PASSED:
- PayPal Developer Webhook Events did not show the expected checkout or payment completion event.
- Render logs did not show POST /v1/billing/paypal/webhook.
- Automatic paid-access activation was not confirmed.

## Safety outcome

The active static PayPal checkout URL was removed from Vercel. Users can no longer pay through the incomplete static PayPal path.

## Conclusion

The static PayPal checkout link is not sufficient for reliable paid-access activation. It can open checkout and complete a sandbox payment, but it does not reliably connect the payment to MeetIQ webhook processing and account activation.

## Recommendation

Replace the static PayPal checkout URL with a backend-generated PayPal checkout/order flow. The backend should create the PayPal checkout session, store MeetIQ user/account context, and activate paid access only after a verified PayPal webhook is received.
