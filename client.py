import logging
import os

from slack import WebClient

SLACK_API_TOKEN = os.environ["SLACK_API_TOKEN"]

logging.info("Setting up Slack WebClient")
client = WebClient(
    token=SLACK_API_TOKEN,
)
