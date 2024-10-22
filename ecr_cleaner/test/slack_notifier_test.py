# -*- coding: utf-8 -*-
import logging

import pytest
from slack_sdk.errors import SlackApiError

from ecr_cleaner import config


def test_send_message_success(slack_notifier, mocker):
    mock_slack_client = mocker.patch.object(
        slack_notifier.slack_client, "chat_postMessage"
    )

    mock_slack_client.return_value = {"ts": "12345.67890"}

    slack_notifier.send_message("Hello, Slack!")

    mock_slack_client.assert_called_once_with(
        channel=config.SLACK_CHANNEL,
        text="Report",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": "Hello, Slack!"}}
        ],
    )


def test_send_message_split_success(slack_notifier, mocker):
    mock_slack_client = mocker.patch.object(
        slack_notifier.slack_client, "chat_postMessage"
    )

    mock_slack_client.return_value = {"ts": "12345.67890"}

    long_message = "A" * 8000  # 8000 characters to force splitting into 2 parts

    slack_notifier.send_message(long_message)

    assert mock_slack_client.call_count == 2

    mock_slack_client.assert_any_call(
        channel=config.SLACK_CHANNEL,
        text="Report",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "A" * 4000},  # First 4000 characters
            }
        ],
    )

    mock_slack_client.assert_any_call(
        channel=config.SLACK_CHANNEL,
        text="Report",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "A" * 4000,  # Remaining 4000 characters
                },
            }
        ],
    )


def test_send_message_failure(slack_notifier, caplog, mocker):

    mock_slack_client = mocker.patch.object(
        slack_notifier.slack_client, "chat_postMessage"
    )

    error_response = {"error": "invalid_auth"}
    mock_slack_client.side_effect = SlackApiError(
        message="Authentication failed", response=error_response
    )

    with caplog.at_level(logging.ERROR):
        slack_notifier.send_message("Hello, Slack!")
        assert "Error sending message to Slack: invalid_auth" in caplog.text

    mock_slack_client.assert_called_once_with(
        channel=config.SLACK_CHANNEL,
        text="Report",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text": "Hello, Slack!"}}
        ],
    )
