# -*- coding: utf-8 -*-
import os


def str_to_bool(value):
    return value.lower() in {"yes", "y", "true"}


AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
SLACK_TOKEN = os.getenv("SLACK_TOKEN", "MY_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "MY_CHANNEL")
KEEP_MIN_IMAGE_COUNT = int(os.getenv("KEEP_MIN_IMAGE_COUNT", 3))
KEEP_IMAGES_NEWER_THAN_DAYS = int(os.getenv("KEEP_IMAGES_NEWER_THAN_DAYS", 7))
SLACK_MAX_MESSAGE_LENGTH = int(os.getenv("SLACK_MAX_MESSAGE_LENGTH", 4000))

DELETE_ENABLED = str_to_bool(os.getenv("DELETE_ENABLED", "false"))
SLACK_ENABLED = str_to_bool(os.getenv("SLACK_ENABLED", "false"))
