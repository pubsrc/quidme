export AWS_PROFILE=globode-dev
aws sso login
# Run with dev extras so uvicorn is available (not needed in Lambda production)
uv run --extra dev python -m uvicorn payme.api.main:app --reload --host 0.0.0.0 --port 8010