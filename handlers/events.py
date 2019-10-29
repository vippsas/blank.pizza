import os
import logging

from slackeventsapi import SlackEventAdapter

import views
import client
from app import app

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

logging.info("Setting up SlackEventAdapter with Flask instance")
slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app)


@slack_events_adapter.on("reaction_added")
def reaction_added(event_data):
    print(event_data)
    event = event_data["event"]

    emoji = event["reaction"]
    channel = event["item"]["channel"]
    user = event["item_user"]
    timestamp = event["item"]["ts"]

    invitation = views.Invitation(user)
    response = client.chat_postEphemeral(
        channel=channel, user=user, blocks=invitation.get_payload())
    print(response)


@slack_events_adapter.on("error")
def error_handler(err):
    logging.error(err)
    print("ERROR: " + str(err))
