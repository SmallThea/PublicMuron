import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from bases.command_base import Command
from modules.quest.panels.quest_panel import QuestPanel

class QuestSchemas(Schema):
    pass

class QuestCommand(Command):
    name = 'quest'
    schemas = QuestSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        await QuestPanel.create(self.channel,self.sender,self.module.less_panels_mod)