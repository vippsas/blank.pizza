import logging
import os

from playhouse.db_url import connect

#DATABASE_STRING = os.environ["DATABASE"]
DATABASE_STRING = "sqlite:///local.db"

logging.info("Connecting to database")
database = connect(DATABASE_STRING)
