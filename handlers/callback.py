import os
import logging

from flask import request, abort

from app import app

SLACK_API_TOKEN = os.environ["SLACK_API_TOKEN"]

logging.info("Setting up Flask routes")


@app.route("/slack/commands/pizza", methods=["POST"])
def command_handler():
    if not request.form["token"] == SLACK_API_TOKEN:
        abort(401)

    trigger_id = request.form["trigger_id"]

    return '', 200
