from .base_model import BaseModel
from .team import Team

from peewee import CharField, ForeignKeyField


class Channel(BaseModel):
    id = CharField(primary_key=True)
    team = ForeignKeyField(Team, backref="channels")
