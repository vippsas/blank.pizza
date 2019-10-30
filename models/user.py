from peewee import AutoField, CharField, DateTimeField, ForeignKeyField, Model, CompositeKey

from .base_model import BaseModel
from .team import Team


class User(BaseModel):
    id = AutoField(primary_key=True)
    slack_id = CharField()
    team = ForeignKeyField(Team, backref="users")
    name = CharField()

    class Meta:
        indexes = (
            (('slack_id', 'team'), True),
        )
