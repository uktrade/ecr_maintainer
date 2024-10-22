# -*- coding: utf-8 -*-

from ecr_cleaner import config
from ecr_cleaner.cleaner import ECRCleaner


def lambda_handler(event, context):
    cleaner = ECRCleaner(aws_region=config.AWS_REGION, slack_token=config.SLACK_TOKEN)
    cleaner.run_cleanup()
    return {"statusCode": 200, "body": "ECR cleanup completed."}
