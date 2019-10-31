import datetime
from peewee import AutoField, DateTimeField, ForeignKeyField, Model

from .base_model import BaseModel
from .invitation import Invitation


class Reminder(BaseModel):
    id = AutoField(primary_key=True)
    invitation = ForeignKeyField(Invitation, backref="reminders")
    sent_at = DateTimeField(default=datetime.datetime.now)
