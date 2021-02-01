import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from utility.loader import narr, conf
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command,UserField
from objects.item import Stack
from objects.rule import Rule

ALLOWED = [
    conf('staff_roles.administration_leader'),
    conf('staff_roles.administration'),
    conf('staff_roles.moderation_leader'),
    conf('staff_roles.moderation'),
]

PRISON = conf('protect.punished_roles.prison')
ISOLATION = conf('protect.punished_roles.isolation')

class ReleaseSchemas(Schema):
    user = UserField(required=True)

class ReleaseCommand(Command):
    name = 'release'
    schemas = ReleaseSchemas
    args_description = {
        'user':"",
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        user_id = self.args['user']
        target = self.module.guild.get_member(user_id)
        user_roles = [role.id for role in target.roles]
        if (PRISON in user_roles) or (ISOLATION in user_roles): # better to check in the db '__' 
            infraction_recap = await self.module.api.release_user(target, self.sender)
            await self.can(narr('protect.release_command_end').format(name=target.display_name))
            await self.module.release(target,context='earlier')
    
            await self.module.log_infraction_release(target, infraction_recap)
        else:
            return await self.cant(narr('protect.not_in_prison'))