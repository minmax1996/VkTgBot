import config
from peewee import *

DATABASE=SqliteDatabase(config.dbname)

class User(Model):
    vkid=IntegerField()
    chatid=IntegerField()
    tname=CharField()

    class Meta:
        database = DATABASE
