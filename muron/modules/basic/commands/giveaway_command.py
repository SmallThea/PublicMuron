import discord
import asyncio
from marshmallow import Schema,fields

from utility.loader import narr
from bases.command_base import Command
from bases.panel_base import AllreadyOnePanelException
from modules.basic.panels.giveaway_panel import GiveawayPanel

class InvSchemas(Schema):
    pass

class InvCommand(Command):
    name = 'inv'
    schemas = InvSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        await GiveawayPanel.create(self.channel,self.sender,self.module.less_panels_mod)

#  'duration'
#   'winners'
#   'price_name'
#   'role_condition'