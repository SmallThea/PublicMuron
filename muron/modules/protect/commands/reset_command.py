import discord
import asyncio
from marshmallow import Schema,fields,validate
import os

from utility.loader import narr, conf
from bases.command_base import Command,UserField

SECURITY_PWD = conf('security_pwd')
STAFF_ROLES = conf('staff_roles').values()
ALLOWED = [
    conf('staff_roles.administration_leader'),
]

async def re_init_user(module, user):
    db_user = module.api.db_user(user) # create the user
    to_remove = [role for role in user.roles if (role != module.guild.default_role) and (role.id not in STAFF_ROLES)]
    await module.shared_remove_user_roles(user, *to_remove) # remove old roles
    default_roles = [module.guild.get_role(role_id) for role_id in conf('separator_roles')] # add separators roles
    default_roles.append(module.guild.get_role(db_user.rank.role_id)) # add rank base role
    await module.shared_add_user_roles(user, *default_roles)

async def after_reset(module):
    for panel in module.all_panels:
        await panel.disable(delete=True)
    # await module.main_bot.module_method('on_ready')


class ResetSchemas(Schema):
    target = UserField()
    pwd = fields.Str(required=True,validate=validate.OneOf((SECURITY_PWD,)))

class ResetallSchemas(Schema):
    pwd = fields.Str(required=True,validate=validate.OneOf((SECURITY_PWD,)))

class ResetallCommand(Command):
    name = 'resetall'
    schemas = ResetallSchemas
    args_description = {
        'pwd': "",
    }
    minArgs = 1

    allowed_channels = []
    allowed_roles = [*ALLOWED]
    banned_roles = []
    dm_only = False

    async def run(self):
        await self.module.api.delete_all_users() # delete everybody
        for user in self.module.guild.members:
            if user.bot:
                continue
            await re_init_user(self.module, user) # recreate user and give roles
        await after_reset(self.module)
        await self.can(narr('resetall_command.success'))

class ResetCommand(Command):
    name = 'reset'
    description = ''
    schemas = ResetSchemas
    args_description = {
        'target':"",
        'pwd': "",
    }
    minArgs = 2

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        target_id = self.args['target']
        await self.module.api.delete_user(target_id)
        target = self.module.guild.get_member(target_id)
        if target is not None:
            if target.bot:
                return await self.cant()
            await re_init_user(self.module, target)
            await after_reset(self.module)
        await self.can(narr('reset_command.success').format(name=f'<@{target_id}>'))