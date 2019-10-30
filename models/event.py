from peewee import AutoField, BooleanField, DateTimeField, ForeignKeyField

from .base_model import BaseModel
from .channel import Channel
from .venue import Venue


class Event(BaseModel):
    id = AutoField(primary_key=True)
    channel = ForeignKeyField(Channel, backref="events")
    venue = ForeignKeyField(Venue)
    starts_at = DateTimeField()
    finalized = BooleanField(default=False)
