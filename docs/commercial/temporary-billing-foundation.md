# Temporary billing foundation

This branch adds the internal billing foundation for MeetIQ before connecting
Stripe, PayPal, or Square.

## Internal plan model

MeetIQ uses an internal effective plan instead of reading upload access directly
from a payment provider.

Current plans:

- `free_trial`
- `paid_pro`

Payment providers should update MeetIQ billing records. Product limits should
read from MeetIQ's internal billing state.

## Temporary launch path

While Stripe activation is pending:

1. PayPal can become the primary temporary payment option.
2. Square can become the backup payment option.
3. ACH, bank transfer, or Zelle can be handled through manual admin override.
4. Stripe can become the primary checkout provider after activation.

## Current endpoints

- `GET /v1/billing/status`
- `POST /v1/admin/billing/manual-upgrade`
- `POST /v1/admin/billing/manual-cancel`

## Next PRs

1. PayPal webhook verification and event mapping.
2. Square webhook verification and event mapping.
3. Pricing/payment funnel in the frontend.
4. Upload-limit integration with `paid_pro` access.
