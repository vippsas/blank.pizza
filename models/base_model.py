from peewee import Model, Proxy
from database import database


class BaseModel(Model):
    class Meta:
        database = database
