import discord
import threading
import functools
import time
import asyncio
import uuid

from datetime import datetime
import traceback

from utility.loader import narr, conf
from utility.emoji import str_to_emoji

ERROR_PATH = conf('error_log_path')
DO_RAISE_ERROR = False


def shared_method(func):
    """Make a method usable and awaitable from the MainBot async loop"""
    @functools.wraps(func)
    async def inner(self, *args, **kwargs):
        self.last_req = time.time()
        task_id = str(uuid.uuid1())
        self.tasks[task_id] = func(self, *args, **kwargs)
        return await self.task_finished(task_id)
    return inner

def log_error():
    with open(ERROR_PATH, 'a+') as f:
        f.write(f"{datetime.now()}\n{traceback.format_exc()}\n\n")


class ModuleBot(discord.Client):

    is_ready = False
    last_req = 0
    tasks = None
    results = None
    errors = None

    def __lt__(self, other):
        return self.last_req < other.last_req

    def __init__(self, token):
        self.tasks = {}
        self.results = {}
        self.errors = {}
        self.loop = asyncio.new_event_loop()

        intent = discord.Intents.default()
        intent.members = True
        discord.Client.__init__(self, intents=intent, loop=self.loop)
        # (self.start(token))#(self.start_bot(token))
        self.loop.create_task(self.start_bot(token))
        thread = threading.Thread(target=self.loop.run_forever)
        thread.start()

    @property
    def on(self):
        return getattr(self, '_on', False)

    async def start_bot(self, token):
        await self.start(token)

    async def on_ready(self):
        if self.on: # security against restarts
            return
        self._on = True

        self.is_ready = True
        self.loop.create_task(self._intern_loop())

    # TODO: in case of bug pub me back inside on_ready without create_task
    async def _intern_loop(self):
        while True:
            await asyncio.sleep(0.01)
            await self.check_tasks()

    async def check_tasks(self):
        for task_id, task in self.tasks.copy().items():
            try:
                self.results[task_id] = await task
            except Exception as e:
                log_error()
                self.errors[task_id] = e
            del self.tasks[task_id]

    async def task_finished(self, task_id):
        while (task_id in self.tasks):
            await asyncio.sleep(0.01)

        if task_id in self.errors:
            error = self.errors[task_id]
            del self.errors[task_id]
            if DO_RAISE_ERROR:
                raise error

        if task_id in self.results:  # condition here because of try catch inside check_tasks
            result = self.results[task_id]
            del self.results[task_id]
            return result

    async def ready(self):
        while not self.is_ready:
            await asyncio.sleep(0.01)

    """
    Redefine all 'shared' methods right bellow
    """

    """
    Message stuff
    """

    @shared_method
    async def send(self, channel, *args, **kwargs):
        state = channel._state
        channel._state = self._connection
        msg = await channel.send(*args, **kwargs)
        channel._state = state
        return msg

    @shared_method
    async def delete_message(self, message, *args, **kwargs):
        # Because of delayed delete, we can't juste change the state, so we use http in this case !
        
        self.main_bot.ignored_delete.append(message.id) # not logging what is deleted by bots

        delay = kwargs.get('delay', None)
        if delay is not None:
            async def delete():
                await asyncio.sleep(delay)
                try:
                    await self._connection.http.delete_message(message.channel.id, message.id)
                except discord.errors.HTTPException:
                    pass

            asyncio.ensure_future(delete(), loop=self._connection.loop)
        else:
            await self._connection.http.delete_message(message.channel.id, message.id)

    @shared_method
    async def edit_message(self, message, *args, **kwargs):
        state = message._state
        message._state = self._connection
        await message.edit(*args, **kwargs)
        message._state = state

    """
    Reaction stuff
    """

    @shared_method
    async def add_reaction(self, message, emoji):
        if isinstance(emoji, str):
            emoji = str_to_emoji(emoji, self)
        state = message._state
        message._state = self._connection
        r = await message.add_reaction(emoji)
        message._state = state
        return r

    @shared_method
    async def remove_reaction(self, reaction, user):
        message = reaction.message
        state = message._state
        state2 = user._state
        user._state = self._connection
        message._state = self._connection
        await message.remove_reaction(reaction.emoji, user)
        message._state = state
        user._state = state2

    @shared_method
    async def clear_reaction(self, reaction):
        message = reaction.message
        state = message._state
        message._state = self._connection
        await reaction.clear()
        message._state = state

    @shared_method
    async def clear_reactions(self, message):
        state = message._state
        message._state = self._connection
        await message.clear_reactions()
        message._state = state

    """ 
    Channel stuff
    """

    @shared_method
    async def get_user_dm(self, user):
        #FIXME: done weirdly but does not work with normal method '__' try to understand why latter
        state = user._state
        user._state = self._connection
        found = user.dm_channel
        if found is not None:
            return found
        data = await user._state.http.start_private_message(user.id)
        output = user._state.add_dm_channel(data)
        user._state = state
        return output

    @shared_method
    async def create_voice_channel(self, guild, *args, **kwargs):
        state = guild._state
        guild._state = self._connection
        chan = await guild.create_voice_channel(*args, **kwargs)
        guild._state = state
        return chan

    @shared_method
    async def create_text_channel(self, guild, *args, **kwargs):
        state = guild._state
        guild._state = self._connection
        chan = await guild.create_text_channel(*args, **kwargs)
        guild._state = state
        return chan

    @shared_method
    async def create_category_channel(self, guild, *args, **kwargs):
        state = guild._state
        guild._state = self._connection
        chan = await guild.create_category_channel(*args, **kwargs)
        guild._state = state
        return chan

    @shared_method
    async def delete_channel(self, channel, *args, **kwargs):
        state = channel._state
        channel._state = self._connection
        await channel.delete(*args, **kwargs)
        channel._state = state

    @shared_method
    async def edit_channel(self, channel, *args, **kwargs):
        overwrites = kwargs.get('overwrites', None)
        if (overwrites is not None) and (len(overwrites) == 0):
            print("Du a des bugs d'API discord tu ne peux pas edit des perms de salon via un dict vide (il faut des perms de base)")
        state = channel._state
        channel._state = self._connection
        await channel.edit(*args, **kwargs)
        channel._state = state

    @shared_method
    async def purge_channel(self, channel, *args, **kwargs):
        state = channel._state
        channel._state = self._connection
        await channel.purge(*args, **kwargs)
        channel._state = state

    @shared_method
    async def delete_messages(self,channel,messages):
        state = channel._state
        channel._state = self._connection
        await channel.delete_messages(messages)
        channel._state = state
    """
    Voc stuff
    """
    @shared_method
    async def move_user(self, user, channel):
        state = user._state
        user._state = self._connection
        if channel:
            state2 = channel._state
            channel._state = self._connection
        await user.move_to(channel)
        user._state = state
        if channel:
            channel._state = state2

    """
    Moderation stuff
    """
    @shared_method
    async def kick_user(self, guild, user, *args, **kwargs):
        state = guild._state
        guild._state = self._connection
        await guild.kick(user, *args, **kwargs)
        guild._state = state

    @shared_method
    async def ban_user(self, guild, user, *args, **kwargs):
        state = guild._state
        state_2 = user._state
        guild._state = self._connection
        user._state = self._connection
        await guild.ban(user, *args, **kwargs)
        guild._state = state
        user._state = state_2

    @shared_method
    async def unban_user(self, guild, user, *args, **kwargs):
        state = guild._state
        state_2 = user._state
        guild._state = self._connection
        user._state = self._connection
        await guild.unban(user, *args, **kwargs)
        guild._state = state
        user._state = state_2

    """
    Roles stuff
    """
    @shared_method
    async def add_user_roles(self, user, *roles):
        state = user._state
        user._state = self._connection
        await user.add_roles(*roles)
        user._state = state

    @shared_method
    async def remove_user_roles(self, user, *roles):
        state = user._state
        user._state = self._connection
        await user.remove_roles(*roles)
        user._state = state

    """
    Divers stuff
    """
    @shared_method
    async def fetch_channel_message(self, channel, message_id):
        state = channel._state
        channel._state = self._connection
        msg = await channel.fetch_message(message_id)
        channel._state = state
        return msg

    @shared_method
    async def fetch_user_by_id(self, user_id):
        return await self.fetch_user(user_id)



class Module(ModuleBot):  # merge with moduleBot
    main_bot = None
    commands = None
    panels = None
    under_modules = None
    api = None
    name = None

    def __init__(self, main_bot, api):
        try:
            self.name = self.__class__.__name__.replace('Module', '').lower()
            token = conf(f'tokens.{self.name}')
        except:
            print(
                f"{self.__class__.__name__} don't have token association in config file !")
            raise Exception
        else:
            ModuleBot.__init__(self, token)
            self.main_bot = main_bot
            self.api = api
            self.commands = []
            self.panels = []
            self.under_modules = []
            self._define_shared()

    def _define_shared(self):
        """Define all the shared methods"""
        for method_name in self.main_bot.shared_methods:
            self._under_scope(method_name)

    def _under_scope(self, method_name):
        # Without this it does not work, because of scopes
        async def method(*args, **kwargs):
            return await getattr(self.main_bot, method_name)(*args, **kwargs)
        setattr(self, method_name, method)

    @property
    def guild(self):
        return self.main_bot.guild

    @property
    def all_panels(self):
        return self.main_bot.all_panels

    @property
    def in_voc(self):
        return self.main_bot.in_voc

    @property
    def available_mod_bot(self):
        return self.main_bot.available_mod_bot

    @property
    def less_panels_mod(self):
        return self.main_bot.less_panels_mod


    def add_command(self, command):
        self.commands.append(command)

    def get_emoji(self, name):
        return str_to_emoji(f':{name}:', self)

    def module_by_name(self,name):
        return self.main_bot.module_by_name(name)

    async def send_notification(self, user, message, color=None):
        channel = self.guild.get_channel(conf('notification_channel'))
        embed = discord.Embed(description=message)
        if color is not None:
            embed.color = color
        await self.send(channel, user.mention, embed=embed)

    async def trigger_hook(self, hook_name, user, *args, **kwargs):
        """Hook trigger system"""
        quest_module = self.module_by_name('quest')
        return await quest_module.handle_hook(hook_name, user, *args, **kwargs)