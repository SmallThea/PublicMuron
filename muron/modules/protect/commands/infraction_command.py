import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from utility.loader import narr, conf
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command,UserField
from objects.item import Stack
from objects.rule import Rule
from modules.protect.panels.infraction_panel import InfractionPanel 

ALLOWED = [
    conf('staff_roles.administration_leader'),
    conf('staff_roles.administration'),
    conf('staff_roles.moderation_leader'),
    conf('staff_roles.moderation'),
] # allowed roles are also protected

INFRACTION_ROLES = [
    conf('protect.punished_roles.prison'),
    conf('protect.punished_roles.isolation'),
]

"""
Remove for the permanent version
"""

class InfractionSchemas(Schema):
    user = UserField(required=True)
    rule_id = fields.Int(required=True,validate=validate.Range(min=0, max=len(Rule.rules())-1)) #FIXME: enelever -1 si exclusif de base

class InfractionCommand(Command):
    name = 'infraction'
    schemas = InfractionSchemas
    args_description = {
        'user':"",
        'rule_id':"",
    }
    minArgs = 2

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        user_id = self.args['user']
        rule_id = self.args['rule_id']

        target = self.module.guild.get_member(user_id)
        user_roles = [role.id for role in target.roles]
        if len(list(set(ALLOWED).intersection(user_roles))):
            return await self.cant(narr('protect.protected_role'))
        if len(list(set(INFRACTION_ROLES).intersection(user_roles))):
            return await self.cant(narr('protect.allready_punished'))
        await InfractionPanel.create(self.channel,self.sender,self.module,target,rule_id)


