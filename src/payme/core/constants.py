"""Application and Stripe-related constants."""


class StripeAccountStatus:
    """Stripe Connect account lifecycle (stored in stripe-accounts table)."""

    NEW = "NEW"
    RESTRICTED = "RESTRICTED"
    VERIFIED = "VERIFIED"
