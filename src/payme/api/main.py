"""Payme API application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from payme.api.dependencies import STRIPE_ACCOUNT_REQUIRED_ERROR_CODE
from payme.api.v1.routes import (
    accounts,
    health,
    metrics,
    payment_links,
    platform,
    refunds,
    stripe_subscriptions,
    subscriptions,
    transactions,
    transfers,
    webhooks,
)
from payme.core.settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="payme", version="0.1.0")

# CORS: read from param config (e.g. SSM), default to *
cors_value = (settings.cors_allowed_origins or "*").strip()
origins = [origin.strip() for origin in cors_value.split(",") if origin.strip()]
allow_all = "*" in origins or cors_value == "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers under /api/v1 (health, accounts, payment-links, subscriptions)
API_V1_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(metrics.router, prefix=API_V1_PREFIX)
app.include_router(accounts.router, prefix=API_V1_PREFIX)
app.include_router(platform.router, prefix=API_V1_PREFIX)
app.include_router(payment_links.router, prefix=API_V1_PREFIX)
app.include_router(subscriptions.router, prefix=API_V1_PREFIX)
app.include_router(transactions.router, prefix=API_V1_PREFIX)
app.include_router(transfers.router, prefix=API_V1_PREFIX)
app.include_router(refunds.router, prefix=API_V1_PREFIX)
app.include_router(stripe_subscriptions.router, prefix=API_V1_PREFIX)
# Webhooks stay at /webhooks/stripe (no version prefix) for stable Stripe callback URL
app.include_router(webhooks.router)


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException):
    # 403 Stripe account required: return the payload as the response body (no "detail" wrapper) for frontend redirect
    if (
        exc.status_code == 403
        and isinstance(exc.detail, dict)
        and exc.detail.get("error_code") == STRIPE_ACCOUNT_REQUIRED_ERROR_CODE
    ):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
def unhandled_exception_handler(_, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
