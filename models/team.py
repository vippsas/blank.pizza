from .base_model import BaseModel

from peewee import CharField


class Team(BaseModel):
    id = CharField(primary_key=True)
