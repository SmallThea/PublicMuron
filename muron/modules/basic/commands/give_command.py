import discord
import asyncio
import datetime
from marshmallow import Schema,fields

from utility.loader import narr, conf
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command,UserField
from objects.item import Stack

ALLOWED = [
    conf('staff_roles.administration_leader'),
]


"""
Remove for the permanent version
"""

class GiveSchemas(Schema):
    user = UserField(required=True)
    item_name = fields.Str(required=True)
    quantity = fields.Int(required=True)

class GiveCommand(Command):
    name = 'give'
    schemas = GiveSchemas
    args_description = {
        'user':"",
        'item_name':"",
        'quantity':"",
    }
    minArgs = 3

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        try:
            stack = Stack(self.args['item_name'],self.args['quantity'])
        except:
            await self.cant()
        else:
            await self.module.api.add_stacks(self.args['user'],stack)
            await self.can()

