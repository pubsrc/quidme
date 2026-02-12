"""Cognito User Pool admin operations (e.g. delete user for account deletion)."""

from __future__ import annotations

import boto3

from payme.core.settings import settings


def delete_user(username: str) -> None:
    """
    Delete a user from the Cognito User Pool (admin_delete_user).
    username should be the Cognito sub (external identifier from JWT).
    Raises ClientError on failure (e.g. user not found, not authorized).
    """
    client = boto3.client(
        "cognito-idp",
        region_name=settings.cognito_region,
    )
    client.admin_delete_user(
        UserPoolId=settings.cognito_user_pool_id,
        Username=username,
    )
