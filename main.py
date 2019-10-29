#!/usr/bin/env python3

import logging
import os
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":

    import app
    import client
    import handlers
    import database
    import models
    import views

    PORT = os.environ["PORT"]

    logging.info("Creating tables")
    db = database.database
    with db:
        db.create_tables([models.Venue, models.Event,
                          models.Invitation, models.Reminder])

    logging.info(f"Starting Slack app on port {PORT}")

    flask_app = app.app
    flask_app.run(port=PORT)
