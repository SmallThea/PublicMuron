import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from bases.command_base import Command
from modules.basic.panels.bank_panel import BankPanel


class BankSchemas(Schema):
    pass

class BankCommand(Command):
    name = 'bank'
    schemas = BankSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        await BankPanel.create(self.channel,self.sender,self.module.less_panels_mod)