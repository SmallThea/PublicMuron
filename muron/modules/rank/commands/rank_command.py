import discord
import asyncio
from marshmallow import Schema,fields

from utility.loader import narr
from bases.command_base import Command
from modules.rank.panels.rank_panel import RankPanel

class RankSchemas(Schema):
    pass

class RankCommand(Command):
    name = 'rank'
    schemas = RankSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        await RankPanel.create(self.channel,self.sender,self.module.less_panels_mod)