import discord
import asyncio
from marshmallow import Schema,fields

from utility.loader import narr
from bases.command_base import Command
from bases.panel_base import AllreadyOnePanelException
from modules.basic.panels.inv_panel import InvPanel

class HelpSchemas(Schema):
    pass

class HelpCommand(Command):
    name = 'help'
    schemas = HelpSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        embed = discord.Embed(colour=discord.Colour.blurple(), description="")
        for module in self.module.main_bot.modules:
            for command in module.commands:
                if len(command.allowed_roles) == 0: # not a staff command
                    embed.description += f"``!{command.name}`` : {command.description_from_name(command.name)}\n"
        await self.module.send(self.channel, self.sender.mention, embed=embed)