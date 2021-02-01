import discord
import asyncio
from marshmallow import Schema,fields,validate
import os

from utility.loader import narr, conf
from bases.command_base import Command,UserField

ERROR_PATH = conf('error_log_path')

ALLOWED = [
    conf('staff_roles.administration_leader'),
]

class ErrorSchemas(Schema):
    action = fields.Str(required=True,validate=validate.OneOf(('show','clear')))

class ErrorCommand(Command):
    name = 'error'
    schemas = ErrorSchemas
    args_description = {
        'action': "",
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        action = self.args['action']
        
        # check if logs exists
        if not os.path.exists(ERROR_PATH):
            return await self.module.send(self.channel, self.sender.mention, embed=discord.Embed(
                description=narr(f'error_command.no_logs')
            ))

        # send log to dms
        dm = await self.module.get_user_dm(self.sender)
        await self.module.send(dm, file=discord.File(ERROR_PATH))

        # clear logs if asked
        if action == 'clear':
            os.remove(ERROR_PATH)
        
        # send the validation message
        await self.module.send(self.channel, self.sender.mention, embed=discord.Embed(
            description=narr(f'error_command.{action}')
        ))