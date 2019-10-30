import os
import logging
import json

from flask import request, abort, jsonify

from app import app
from client import client as slack

from models import Invitation, InvitationState

import api.manager


logging.info("Setting up Flask routes for interactive components")


@app.route("/slack/interactions", methods=["POST"])
def interactions_handler():
    # TODO: Validation

    payload = json.loads(request.form["payload"])
    print(payload)

    if payload["type"] == "block_actions":
        if not len(payload["actions"]) == 1:
            print("Not 1 action")
            abort(400)

        action = payload["actions"][0]
        if not action["value"] in [InvitationState.Accepted, InvitationState.Rejected]:
            print("Wrong value")
            abort(400)

        channel = payload["container"]["channel_id"]
        timestamp = payload["container"]["message_ts"]
        invitation = Invitation.get_or_none(
            (Invitation.slack_channel == channel) & (Invitation.slack_ts == timestamp))
        if not invitation:
            print("No invitation")
            abort(400)

        api.manager.update_invitation(invitation, action["value"])
        api.manager.finalize_events()

    return '', 200
