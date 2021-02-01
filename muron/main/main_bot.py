import discord
import time
import asyncio

from utility.loader import conf, narr
from utility.emoji import load_custom_emojis, emoji_to_str
from api.api import Api
from modules.basic.basic_module import BasicModule
from modules.rank.rank_module import RankModule
from modules.activity.activity_module import (
    ActivityModule, 
    FishingModule,
    MiningModule,
    PickingModule,
    AnimalHuntingModule,
    DiggingModule,
    InsectHuntingModule,
    ExplorationModule,
    # NecromancyModule,
    )
from modules.welcome.welcome_module import WelcomeModule
from modules.economy.economy_module import EconomyModule
from modules.voc.voc_module import VocModule
from modules.protect.protect_module import ProtectModule
from modules.quest.quest_module import QuestModule


# ALT 255 => espace pris en compte par discord


GUILD_ID = conf('guild_id')
PREFIX = conf('prefix')
ENABLED_MODULES = [
    BasicModule,
    ActivityModule,
    FishingModule,
    MiningModule,
    PickingModule,
    AnimalHuntingModule,
    DiggingModule,
    InsectHuntingModule,
    ExplorationModule,
    # NecromancyModule,
    RankModule,
    WelcomeModule,
    EconomyModule,
    VocModule,
    ProtectModule,
    QuestModule,
]


class MainBot(discord.Client):
    prefix = PREFIX

    api = None
    modules = []
    in_voc = {}  # user:{start:, duration:, actif:, }
    ignored_delete = [] # message wich should not trigger on_message_delete when deleted (delete by bot)

    shared_methods = [
        'shared_send',
        'shared_delete_message',
        'shared_add_reaction',
        'shared_remove_reaction',
        'shared_clear_reaction',
        'shared_clear_reactions',
        'shared_move_user',
        'shared_edit_channel',
        'shared_delete_channel',
        'shared_create_voice_channel',
        'shared_purge_channel',
        'shared_fetch_channel_message',
        'shared_fetch_user_by_id',
        'shared_kick_user',
        'shared_ban_user',
        'shared_unban_user',
        'shared_add_user_roles',
        'shared_remove_user_roles',
        'shared_delete_messages',
        'shared_create_user_dm',
    ]

    def __init__(self):
        intent = discord.Intents.default()
        intent.members = True
        discord.Client.__init__(self, intents=intent)

    @classmethod
    def run_bot(cls):
        """Blocking function that run the main bot"""
        main_bot = MainBot()
        main_bot.run(conf('tokens.main'))

    @property
    def on(self):
        return getattr(self, '_on', False)

    @property
    def guild(self):
        return self.get_guild(GUILD_ID)

    async def on_ready(self):
        if self.on:
            return
        load_custom_emojis(self)
        self._define_shared()
        self.api = Api(self)
        await self.load_modules()
        await self.module_method('on_ready')
        self._on = True

        self.loop.create_task(self.voice_handler())
        self.loop.create_task(self.panel_auto_remover())
        print("Muron ON")

    """
    Trucs de modules
    """
    @property
    def all_panels(self):
        panels = []
        for module in self.modules:
            panels += [panel for panel in module.panels]
        return panels

    @property
    def available_mod_bot(self):
        """Return the module that don't do a action for the longest time"""
        mods = list([mod for mod in self.modules])
        mods.sort()
        return mods[0]

    @property
    def less_panels_mod(self):
        """Return a module with the less panels"""
        mods = list([mod for mod in self.modules])
        mods.sort(key=lambda mod: len(mod.panels))
        return mods[0]

    async def module_method(self, method_name, *args):
        """Call the method from the module on_ready ==> _on_ready """
        method_name = f'_{method_name}'
        for module in self.modules:
            method = getattr(module, method_name, False)
            if method:
                await method(*args)

    async def load_modules(self):
        """Load all modules"""
        for module in ENABLED_MODULES:
            module = module(self, self.api)
            self.modules.append(module)

        for module in self.modules:
            await module.ready()

    def _define_shared(self):
        """Define all the shared methods"""
        for method_name in self.shared_methods:
            self._under_scope(method_name)

    def _under_scope(self, method_name):
        # Without this it does not work, because of scopes
        mod_method_name = method_name.replace('shared_', '')

        async def method(*args, **kwargs):
            mod = self.available_mod_bot
            return await getattr(mod, mod_method_name)(*args, **kwargs)
        setattr(self, method_name, method)

    def module_by_name(self,name):
        for module in self.modules:
            if module.name == name:
                return module
        raise Exception(f'No module with name : {name}')

    """
    Gestionnaire de commandes
    """

    async def command_handler(self, msg_data):
        """pour le moment les commands sont autorisé uniquement sur le serveur et pas en dm (voir Muron.on_message)"""
        command_name = msg_data.content[1:].split(' ')[:1][0]
        args = msg_data.content[1:].split(' ')[1:]

        command_data = {
            'arg_list': args,
            'sender': msg_data.author,
            'channel': msg_data.channel,
            'dm': (msg_data.guild is None),
            'bot': self,
            'message': msg_data,
        }

        for module in self.modules:
            for command in module.commands:
                if command.name == command_name:
                    command_data['module'] = module
                    c = command(**command_data)
                    return await c.intern_run()
        # unknown command


    """
    Leave, join and invitation stuff
    """
    async def on_member_join(self, member):
        await self.module_method('on_member_join', member)

    async def on_member_remove(self, member):
        await self.module_method('on_member_remove', member)

    async def on_invite_create(self, invite):
        await self.module_method('on_invite_create', invite)

    async def on_invite_delete(self, invite):
        await self.module_method('on_invite_delete', invite)

    """
    Command interne utiles
    """

    async def on_message(self, message):
        if (not self.on) or message.author.bot or (message.guild != self.guild):
            return

        if (message.content[:1] == self.prefix):
            return await self.command_handler(message)

        for module in self.modules:
            for panel in module.panels[:]:
                if panel.is_waiting_input:
                    if panel.message.channel == message.channel:
                        if panel.user == message.author:
                            panel.is_waiting_input = False
                            await self.shared_delete_message(message)
                            await panel._input_handling(message.content)

        await self.module_method('on_message', message)

    async def on_bulk_message_delete(self, messages):
        if (not self.on) or (messages[0].guild != self.guild):
            return

        for message in messages:
            if message.author.bot:
                for panel in self.all_panels:
                    if panel.message.id == message.id:
                        panel.is_disable = True
        
        # await self.module_method('on_bulk_message_delete', messages)


    async def on_message_delete(self, message):
        if (not self.on) or (message.guild != self.guild):
            return

        if message.author.bot:
            for panel in self.all_panels:
                if panel.message.id == message.id:
                    panel.is_disable = True
            return 

        try:
            self.ignored_delete.remove(message.id)
        except ValueError:
            pass
        else:
            return # skip and delete if the message should be ignored

        await self.module_method('on_message_delete', message)


    """
    Voice state handler
    """

    async def voice_handler(self):
        minutes_loop = 0
        while True:
            start = time.time()
            await asyncio.sleep(1)
            past_time = (time.time() - start)
            minutes_loop += past_time
            for data in self.in_voc.values():
                if data['active']:
                    data['duration'] += 1  # past_time
            if minutes_loop > 60:
                module = self.available_mod_bot
                for user in self.in_voc.keys():
                    await module.trigger_hook('in_voc',user,minutes_loop)
                minutes_loop = 0

    async def on_guild_channel_delete(self, channel):
        if (not self.on) or (channel.guild != self.guild):
            return
        await self.module_method('on_guild_channel_delete', channel)

    async def on_guild_channel_create(self, channel):
        if (not self.on) or (channel.guild != self.guild):
            return
        await self.module_method('on_guild_channel_create', channel)

    async def on_guild_channel_update(self, before, after):
        if (not self.on) or (after.guild != self.guild):
            return
        await self.module_method('on_guild_channel_update', before, after)

    async def on_voice_state_update(self, user, before, after):
        # active user handling
        if (not self.on):
            return
        # if no one of the voc is inside the guild
        if not ((before.channel and (before.channel.guild == self.guild)) or (after.channel and (after.channel.guild == self.guild))):
            return

        active = not after.self_deaf
        if self.in_voc.get(user) is None:  # not already in voc
            if after.channel is not None:
                self.in_voc[user] = {
                    'start': time.time(), 'duration': 0, 'active': active}
        else:  # already in voc
            if after.channel is None:
                del self.in_voc[user]
            else:
                self.in_voc[user]['active'] = active

        await self.module_method('on_voice_state_update', user, before, after)

    """
    Panel handler
    """

    async def panel_auto_remover(self):
        """Check for disables panel and delete them every DT"""
        while True:
            await asyncio.sleep(0.1)
            for module in self.modules:
                for p in module.panels[:]:
                    if p.is_disable:
                        module.panels.remove(p)

    async def on_reaction_add(self, reaction, user):
        if (not self.on) or (user.bot) or (reaction.message.channel.guild != self.guild):
            return

        for module in self.modules:
            for p in module.panels[:]:
                if p.is_disable:
                    continue  # module.panels.remove(p)
                else:
                    if reaction.message.id != p.message.id:
                        continue

                    for emoji, data in p.mapping.items():
                        r_emoji = emoji_to_str(reaction.emoji)
                        if emoji == r_emoji:
                            can_reac_func = data.get('can_reac', None)
                            if can_reac_func is None:
                                if p.user is not None:
                                    if user.id != p.user.id:
                                        continue  # if a user is linked to the panel accept only his inputs
                                else:
                                    pass  # if bot no accept function and user in the panel, it accept all inputs
                            else:
                                can_reac = await can_reac_func(user)
                                if not can_reac:
                                    continue  # if the emoji have a on_reac func use it to determine if we accept the input of the user

                            if (not p.in_use) and (not p.is_rendering):
                                p.in_use = True
                                await getattr(p, data['callback'])()
                                await p.use(user, emoji)
                                p.in_use = False
                    if not p.is_disable:
                        await self.shared_remove_reaction(reaction, user)
                    break

        await self.module_method('on_reaction_add', reaction, user)
