# Square billing webhook

This document describes the temporary Square billing webhook for MeetIQ.

## Purpose

Square is the backup temporary payment provider while Stripe activation is pending.

## Endpoint

POST /v1/billing/square/webhook

## Required environment variables
SQUARE_WEBHOOK_SIGNATURE_KEY=
SQUARE_WEBHOOK_NOTIFICATION_URL=

## Test-only environment variable
SQUARE_WEBHOOK_VERIFY_DISABLED=true
This bypass is only honored during pytest runs.

## Events handled

Active paid access:
- payment.updated with payment.status COMPLETED
- invoice.payment_made

Cancellation:
- invoice.canceled
- subscription.canceled

Manual review:
- invoice.refunded
- invoice.scheduled_charge_failed
- refund.created
- refund.updated

## User matching
Preferred temporary pattern:
note = meetiq:user@example.com
description = meetiq:user@example.com
buyer_email_address and invoice primary_recipient.email_address are also accepted.

## Safety rules
- Square webhook signature verification is required outside tests.
- Duplicate Square event IDs are ignored.
- Unmatched payments are stored as failed billing events and do not activate access.
- Refunds and failed charges are recorded for manual review.
