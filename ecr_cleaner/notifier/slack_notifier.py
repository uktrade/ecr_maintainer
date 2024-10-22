# -*- coding: utf-8 -*-
import logging

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ecr_cleaner import config


class SlackNotifier:
    MAX_MESSAGE_LENGTH = config.SLACK_MAX_MESSAGE_LENGTH

    def __init__(self, slack_token):
        self.slack_client = WebClient(token=slack_token)

    def send_message(self, message):
        try:
            # If the message exceeds the Slack limit, split it into smaller chunks
            messages = self._split_message(message)

            for part in messages:
                # Send each part using the new Block Kit with Markdown formatting
                response = self.slack_client.chat_postMessage(
                    channel=config.SLACK_CHANNEL,
                    text="Report",
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": part}}
                    ],
                )

                logging.info(f"Slack message sent: {response['ts']}")

        except SlackApiError as e:
            logging.error(f"Error sending message to Slack: {e.response['error']}")

    def _split_message(self, message):
        """
        Splits a message into chunks that respect Slack's 4000 character limit.
        """
        if len(message) <= self.MAX_MESSAGE_LENGTH:
            return [message]
        else:
            # Split the message into chunks of max length
            return [
                message[i : i + self.MAX_MESSAGE_LENGTH]
                for i in range(0, len(message), self.MAX_MESSAGE_LENGTH)
            ]
