import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from utility.loader import narr, conf
from bases.command_base import Command,UserField
from api.api import AllreadyBanException

ALLOWED = [
    conf('staff_roles.administration_leader'),
    conf('staff_roles.administration'),
    conf('staff_roles.moderation_leader'),
] # allowed is also protected ==> staff leader and admins

class BanSchemas(Schema):
    user = UserField(required=True)
    delete_days = fields.Int()

class BanCommand(Command):
    name = 'ban'
    schemas = BanSchemas
    args_description = {
        'user':"",
        'delete_days':""
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        user_id = self.args['user']
        target = self.module.guild.get_member(user_id)
        
        if 'delete_days' in self.args:
            delete_days = sorted((0,self.args['delete_days'],7))[1]
        else:
            delete_days = 0

        if target is None:
            try:
                await self.module.api.ban(user_id) # can raise AllreadyBanException
                await self.module.log_ban(user_id, self.sender)
            except AllreadyBanException:
                return await self.cant(narr('protect.allready_ban').format(user_id=user_id))
            else:
                await self.can(narr('protect.ban_absent').format(user_id=user_id))
        else:
            user_roles = [role.id for role in target.roles]
            if len(list(set(ALLOWED).intersection(user_roles))) > 0:
                return await self.cant(narr('protect.protected_role'))
            try:
                await self.module.api.ban(target) # set the ban to true
                await self.module.log_ban(user_id, self.sender)
            except AllreadyBanException:
                pass # should never happen
            await self.module.shared_ban_user(self.module.guild,target,delete_message_days=delete_days)
            await self.can(narr('protect.ban_present').format(name=target.mention))