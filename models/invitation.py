from peewee import CharField, ForeignKeyField, Model, AutoField

from .base_model import BaseModel
from .event import Event
from .user import User


class Invitation(BaseModel):
    id = AutoField(primary_key=True)
    event = ForeignKeyField(Event, backref="invitations")
    user = ForeignKeyField(User, backref="invitations")
    state = CharField()  # ref InvitationState
    slack_channel = CharField()
    slack_ts = CharField()
