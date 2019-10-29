from peewee import CharField, ForeignKeyField, Model, AutoField

from .base_model import BaseModel
from .event import Event


class Invitation(BaseModel):
    id = AutoField(primary_key=True)
    event = ForeignKeyField(Event, backref="invitations")
    user = CharField()
    state = CharField()  # ref InvitationState
