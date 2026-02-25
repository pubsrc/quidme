"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Ensure collectors are registered at import time.
from payme.services import metrics as _metrics  # noqa: F401

router = APIRouter(tags=["metrics"])


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
