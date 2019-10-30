import os
import logging

from flask import request, abort, jsonify

from app import app

import api.manager

logging.info("Setting up Flask routes for Slash commands")


@app.route("/slack/commands/pizza", methods=["POST"])
def pizza_command_handler():
    # TODO: Validation
    trigger_id = request.form["trigger_id"]
    print(request.form)

    api.manager.start_pizza(
        request.form["channel_id"], request.form["user_id"])

    return '', 200
