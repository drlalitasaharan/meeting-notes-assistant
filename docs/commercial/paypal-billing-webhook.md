# PayPal billing webhook

This document describes the temporary PayPal billing webhook for MeetIQ.

## Purpose

While Stripe activation is pending, PayPal can be used as the primary temporary payment option. PayPal webhooks update MeetIQ's internal billing state.

## Endpoint

POST /v1/billing/paypal/webhook

## Required environment variables

Sandbox:
PAYPAL_ENV=sandbox
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_WEBHOOK_ID=

Live:
PAYPAL_ENV=live
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_WEBHOOK_ID=

## Test-only environment variable

PAYPAL_WEBHOOK_VERIFY_DISABLED=true

This bypass is only honored during pytest runs.

## Events handled

Active paid access:
- BILLING.SUBSCRIPTION.ACTIVATED
- PAYMENT.SALE.COMPLETED
- PAYMENT.CAPTURE.COMPLETED
- CHECKOUT.ORDER.COMPLETED

Cancellation:
- BILLING.SUBSCRIPTION.CANCELLED
- BILLING.SUBSCRIPTION.CANCELED
- BILLING.SUBSCRIPTION.SUSPENDED

Manual review:
- PAYMENT.SALE.REFUNDED
- PAYMENT.SALE.REVERSED
- PAYMENT.CAPTURE.REFUNDED
- CUSTOMER.DISPUTE.CREATED

## User matching

The webhook tries to match a PayPal payment to a MeetIQ user by email.

Preferred temporary pattern:
custom_id = meetiq:user@example.com

The payer/subscriber email is also accepted when present.

## Safety rules

- PayPal webhook signature verification is required outside tests.
- Duplicate PayPal event IDs are ignored.
- Unmatched payments are stored as failed billing events and do not activate access.
- Refunds, reversals, and disputes are recorded for manual review.
