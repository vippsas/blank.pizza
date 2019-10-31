from peewee import AutoField, CharField, DateTimeField, ForeignKeyField, Model, CompositeKey

from .base_model import BaseModel
from .channel import Channel


class User(BaseModel):
    id = AutoField(primary_key=True)
    slack_id = CharField()
    channel = ForeignKeyField(Channel, backref="users")
    name = CharField()

    class Meta:
        indexes = (
            (('slack_id', 'channel'), True),
        )
