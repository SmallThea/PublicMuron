from mongoengine import connect

from utility.loader import config_mode,conf
config_mode('test')
from main.main_bot import MainBot

connect(conf('database.name'),
    host=conf('database.host'),
    port=conf('database.port'),
    username=conf('database.username'),
    password=conf('database.password'),
    )
MainBot.run_bot()