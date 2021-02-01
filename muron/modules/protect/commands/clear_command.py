import discord
import asyncio
from datetime import datetime,timedelta
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

class ClearSchemas(Schema):
    amount = fields.Int(required=True,validate=validate.Range(min=1,max=99))
    user = UserField()

class ClearCommand(Command):
    name = 'clear'
    schemas = ClearSchemas
    args_description = {
        'amount': "",
        'user':""
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        messages = [self.message,]
        if 'user' in self.args:
            user = self.module.guild.get_member(self.args['user'])
        else:
            user = None

        delete_time_limit = datetime.utcnow() - timedelta(days=14)
        async for message in self.channel.history(limit=999):
            if (user is None) or (message.author == user):
                if message.id == self.message.id:
                    continue
                if message.created_at <= delete_time_limit:
                    break
                if len(messages) >= (self.args['amount']+1):
                    break
                messages.append(message)
        await self.module.shared_delete_messages(self.channel,messages)