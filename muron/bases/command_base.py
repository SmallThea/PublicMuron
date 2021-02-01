import discord

from marshmallow import Schema,ValidationError,fields
from utility.loader import narr, conf
from utility.emoji import str_to_emoji

"""
Custom fields for command creation
"""

class UserField(fields.Field):
    """<@!id>"""

    # def _serialize(self, value, attr, obj, **kwargs):
    #     raise ValidationError

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            if (value[0:3] == '<@!') and (value[-1] == '>'):
                return int(value[3:-1])
            raise Exception
        except:
            raise ValidationError('not a user')

class RoleField(fields.Field):
    """<@&id>"""
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            if (value[0:3] == '<@&') and (value[-1] == '>'):
                return int(value[3:-1])
            raise Exception
        except:
            raise ValidationError('not a role')

class ChannelField(fields.Field):
    """<#id>"""
    def _deserialize(self, value, attr, data, **kwargs):
        try:
            if (value[0:2] == '<#') and (value[-1] == '>'):
                return int(value[2:-1])
            raise Exception
        except:
            raise ValidationError('not a channel')

"""
Command utils
"""

class CommandSchemas(Schema):
    pass


def func(param):
    pass


class Command:
    name = ''
    schemas = CommandSchemas
    args_description = {}
    minArgs = 0

    allowed_channels = conf('command_channels') #[]
    allowed_roles = []
    banned_roles = []
    dm_only = False

    _emoji = None

    @classmethod
    def description_from_name(cls, name):
        """Permit to get the command description without instanciating the command"""
        return narr(f'commands.{name}.desc')

    def get_emoji(self,name):
        return str_to_emoji(f':{name}',self.module)

    @property
    def description(self):
        return self.description_from_name(self.name)

    def __init__(self, arg_list, sender, channel, dm, bot, module, message):
        # argument handling
        args = {}
        if len(arg_list) > 0:
            if len(arg_list) < self.minArgs:
                pass
            
            for k, _ in self.args_description.items():
                if len(args) >= len(arg_list):
                    break
                args[k] = arg_list[len(args)]

        self.sender = sender
        self.channel = channel
        self.dm = dm
        self.bot = bot
        self.module = module
        self.message = message

        self.err = self.schemas().validate(args)
        if len(self.err) > 0:
            self.args = {}
        else:
            command_schemas = self.schemas()
            self.args = command_schemas.load(args)

    async def intern_run(self):
        if len(self.allowed_channels) > 0:
            if self.channel.id not in self.allowed_channels:
                #return await self.module.send(self.channel,'Mauvais channel !')
                return 

        if self.dm_only and not self.dm:
            # return await self.module.send(self.channel,'Uniquement en dm !')
            return 

        sender_roles = [role.id for role in self.sender.roles]
        if len(self.allowed_roles) > 0:
            inter = [r for r in sender_roles if r in self.allowed_roles]
            if len(inter) == 0:
                return await self.module.send(self.channel, self.sender.mention, embed=discord.Embed(
                    description=narr('command.unauthorized')
                ))
        if len(self.banned_roles) > 0:
            inter = [r for r in sender_roles if r in self.banned_roles]
            if len(inter) > 0:
                # return await self.module.send(self.channel,'Accés restreint !')
                return

        if len(self.err) > 0:
            return await self.wrong_usage()
        
        await self.module.shared_delete_message(self.message)
        await self.module.trigger_hook('use_command', self.sender, self.name, self.args)
        return await self.run()

    async def run(self):
        if True:
            raise Exception('You need to overide this function')
        return ''

    async def wrong_usage(self):
        #TODO: faire une méthode interne qui renvoie un message de mauvaise utilisation et une méthode externe propre a chaque commande qui génère le message d'aide en cas de mauvaise utilisation
        # self.err.items()
        return await self.module.send(self.channel, self.sender.mention, embed=discord.Embed(
            description=narr('command.wrong_usage')
        ))

    async def cant(self,message=None):
        embed = discord.Embed(
            colour=discord.Colour.red(),
            description=message or narr('cant'),
        )
        await self.module.send(self.channel,embed=embed)

    async def can(self,message=None):
        embed = discord.Embed(
            colour=discord.Colour.green(),
            description=message or narr('can'),
        )
        await self.module.send(self.channel,embed=embed)