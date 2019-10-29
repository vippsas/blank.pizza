from peewee import CharField, Model, AutoField

from .base_model import BaseModel


class Venue(BaseModel):
    id = AutoField(primary_key=True)
    name = CharField()
