from .base_model import BaseModel
from .team import Team

from peewee import CharField, ForeignKeyField, IntegerField


class Channel(BaseModel):
    id = CharField(primary_key=True)
    team = ForeignKeyField(Team, backref="channels")

    start_preparation = IntegerField()
    participants = IntegerField()
    reminders = IntegerField()
    reminder_interval = IntegerField()
