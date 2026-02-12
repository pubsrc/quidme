from __future__ import annotations

import os

import boto3


def get_dynamodb_resource():
    endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
    region = os.getenv("AWS_REGION", "eu-west-2")
    return boto3.resource("dynamodb", region_name=region, endpoint_url=endpoint_url)
