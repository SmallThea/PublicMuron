import discord
import asyncio
import datetime
from marshmallow import Schema,fields

from utility.loader import narr
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command


USER_INFO_TEMPLATE = """{money_key} : {money} {money_emoji}
{gem_key} : {gems} {gem_emoji}
{level_key} : {level}
{xp_key} : {xp_bar}  {xp}/{xp_needed}
{energy_key} : {energy_bar}  {energy}/{energy_max}
{inviter_key} : {inviter}

{message_key} : {total_message}
{voc_key} : {total_voc}

{voc_session_key} : {voc_session}
"""

class MeSchemas(Schema):
    pass

class MeCommand(Command):
    name = 'me'
    schemas = MeSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        db_user = self.module.api.db_user(self.sender)
        try:
            voc_session = str(datetime.timedelta(seconds=self.module.in_voc[self.sender]['duration']))
        except:
            voc_session = narr('me_command.no_voc_session')
            
        if db_user.inviter is not None:
            user = self.module.get_user(db_user.inviter.user_id)
            if user:
                inviter = user.mention #display_name
            else:
                inviter = narr('me_command.unknown_inviter') + f" [{db_user.inviter.user_id}]"
        else:
            inviter = narr('me_command.no_inviter')
        
        

        format_vars = {
            "money_key":narr('me_command.money_key'),
            "level_key":narr('me_command.level_key'),
            "xp_key":narr('me_command.xp_key'),
            "voc_session_key":narr('me_command.voc_session_key'),
            "message_key":narr('me_command.message_key'),
            "voc_key":narr('me_command.voc_key'),
            "energy_key":narr('me_command.energy_key'),
            "gem_key":narr('me_command.gem_key'),
            "gems":db_user.gems,
            "gem_emoji":str_to_emoji(':gem:',self.module),
            "inviter_key":narr('me_command.inviter'),
            "inviter":inviter,
            "energy":db_user.energy,
            "money_emoji":str_to_emoji(':money:',self.module),
            "money":db_user.money,
            "level":db_user.level,
            "xp":db_user.xp,
            "xp_needed":db_user.xp_needed,
            "xp_bar": emoji_bar(8,db_user.xp/db_user.xp_needed,'🟩','⬛',self.module),
            "energy_bar": emoji_bar(8,db_user.energy/db_user.energy_max,'🟨','⬛',self.module),
            "energy_max":db_user.energy_max,
            "total_message":db_user.message_sent,
            "total_voc":str(datetime.timedelta(seconds=db_user.vocal_time)),
            "voc_session":voc_session,
        }
        embed = discord.Embed(
            title = narr('me_command.title').format(name=self.sender.display_name),
            colour = discord.Colour.blurple(),
            description = USER_INFO_TEMPLATE.format(**format_vars)
        )
        await self.module.send(self.channel, self.sender.mention, embed=embed)