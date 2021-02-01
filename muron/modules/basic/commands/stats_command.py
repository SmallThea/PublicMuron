import discord
import asyncio
import datetime
from marshmallow import Schema, fields

from utility.loader import narr
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command


class StatsSchemas(Schema):
    pass


class StatsCommand(Command):
    name = 'stats'
    schemas = StatsSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        db_user = self.module.api.db_user(self.sender)
        stats_str = "\n".join(
            [f"{narr(f'stats.{stat}')} : {value}" for stat, value in db_user.stats.items()])

        embed = discord.Embed(
            title=narr('stats_command.title').format(
                name=self.sender.display_name),
            colour=discord.Colour.blurple(),
            description=stats_str
        )
        await self.module.send(self.channel, embed=embed)
