from peewee import DateTimeField, ForeignKeyField, AutoField

from .base_model import BaseModel
from .venue import Venue


class Event(BaseModel):
    id = AutoField(primary_key=True)
    venue = ForeignKeyField(Venue)
    starts_at = DateTimeField()
