#!/usr/bin/env python3

import logging
import os
import sys

logging.basicConfig(level=logging.DEBUG)


def debug_init():
    from peewee import EXCLUDED
    from client import client as slack
    from models import Team, Channel, User, Venue

    import api.slack

    logging.info("Creating tables")
    db = database.database
    with db:
        db.create_tables(models.tables)

    logging.info("Creating instances")
    res = slack.team_info()
    team_id = res["team"]["id"]
    conversations = api.slack.get_conversations()
    api.slack.populate_cache()
    for c in conversations:
        team, _ = Team.get_or_create(id=team_id)
        channel = Channel.create(id=c["id"], team=team.id)

        users = api.slack.get_slack_users(channel.id)
        for u in users:
            print(u["name"])
            query = (User
                     .insert(slack_id=u["id"], team=team.id, name=u["name"])
                     .on_conflict(
                         conflict_target=[User.id],
                         preserve=[User.slack_id, User.name]
                     ))
            query.execute()

    logging.info("Creating venues")
    Venue.insert_many([{"name": "Tranen"}, {"name": "Sentralen"}, {
        "name": "Ferro"}, {"name": "Hell's Kitchen"}]).execute()


if __name__ == "__main__":

    import app
    import client
    import handlers
    import database
    import models
    import views

    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        debug_init()

    import api.manager
    api.manager.send_reminders()

    PORT = os.environ["PORT"]

    logging.info(f"Starting Slack app on port {PORT}")

    flask_app = app.app
    flask_app.run(port=PORT)
