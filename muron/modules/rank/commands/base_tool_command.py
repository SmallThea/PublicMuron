import discord
import asyncio
from marshmallow import Schema,fields

from utility.loader import narr
from bases.command_base import Command
from modules.rank.panels.base_tool_panel import BaseToolPanel

class BaseToolSchemas(Schema):
    pass

class BaseToolCommand(Command):
    name = 'basetool'
    schemas = BaseToolSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        await BaseToolPanel.create(self.channel,self.sender,self.module.less_panels_mod)