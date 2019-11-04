import os
import logging

from flask import request, abort, jsonify

from app import app

from models import Channel
import api.manager

logging.info("Setting up Flask routes for Slash commands")


@app.route("/slack/commands/pizza", methods=["POST"])
def pizza_command_handler():
    trigger_id = request.form["trigger_id"]
    print(request.form)

    channel_id = request.form["channel_id"]
    if not Channel.select().where(Channel.id == channel_id).exists():
        return '', 400

    event = api.manager.create_event(channel_id)
    api.manager.trigger_invitations(event)

    return '', 200
