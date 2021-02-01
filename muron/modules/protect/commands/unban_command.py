import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from utility.loader import narr, conf
from bases.command_base import Command,UserField
from api.api import NotAllreadyBanException

ALLOWED = [
    conf('staff_roles.administration_leader'),
    conf('staff_roles.administration'),
    conf('staff_roles.moderation_leader'),
] # allowed is also protected ==> staff leader and admins

class UnbanSchemas(Schema):
    user = UserField(required=True)
    delete_days = fields.Int()

class UnbanCommand(Command):
    name = 'unban'
    schemas = UnbanSchemas
    args_description = {
        'user':"",
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        user_id = self.args['user']
        target = await self.module.shared_fetch_user_by_id(user_id)

        try:
            await self.module.api.unban(user_id)
        except NotAllreadyBanException:
            return await self.cant(narr('protect.allready_unban').format(user_id=user_id))
        else:
            await self.module.shared_unban_user(self.module.guild, target)
            await self.can(narr('protect.unban').format(user_id=user_id))

        await self.module.log_unban(user_id, self.sender)