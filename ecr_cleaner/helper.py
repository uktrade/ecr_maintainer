# -*- coding: utf-8 -*-
import os

import boto3


def get_aws_client(service_name, region_name=None, profile_name=None):
    """
    Dynamically chooses between boto3.client() for Lambda and boto3.session.Session() for local execution.
    If running locally, allows specifying an AWS profile.
    """
    if os.getenv("LAMBDA_TASK_ROOT"):
        # Running in AWS Lambda: use the default boto3.client() (credentials are managed by Lambda)
        return boto3.client(service_name, region_name=region_name)
    else:
        # Running locally: create a session with an optional profile
        session = boto3.session.Session(profile_name=profile_name)
        return session.client(service_name, region_name=region_name)
