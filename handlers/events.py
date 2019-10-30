import os
import logging

from slackeventsapi import SlackEventAdapter

import views
from client import client as slack
from app import app

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

logging.info("Setting up SlackEventAdapter with Flask instance")
slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    event = event_data["event"]
    print(event)

    emoji = event["reaction"]
    if emoji == "pizza":
        slack.reactions_add(
            name=emoji,
            channel=event["item"]["channel"],
            timestamp=event["item"]["ts"]
        )


@slack_events_adapter.on("error")
def error_handler(err):
    logging.error(err)
    print("ERROR: " + str(err))
