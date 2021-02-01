"""
Un panel est un message discord avec des réactions qui permetent l'intéraction avec le message, 
Fonctionnalité attendue : 
- suporter différent formats (message/embed/image)
- pouvoir en créer facilement grace à une base (Panel)
- ajouter des réactions et brancher des callback dessus
- pouvoir edit le message
- pouvoir stocker des actions qui s'éffectue après un certain délai 
- 
"""

import discord
import asyncio
import time
import datetime
import random

from utility.loader import conf, narr
from api.api import Api
from utility.emoji import str_to_emoji, emoji_to_str

class AllreadyOnePanelException(Exception):
    def __init__(self, panel):
        Exception.__init__(self)
        self.panel = panel

class Panel:
    """
    Menu with wich a player can interact, reactions are buttons and trigger action when cliqued by the owner of the panel
    Buttons and display of the panel can be modified while working
    """

    # intern
    is_disable = False
    in_use = False
    is_rendering = False
    is_waiting_input = False
    _emoji = None
    user_values = None  # key ==> value to follow | value ==> value

    # use by childrens
    message = None
    user = None
    module = None
    active_buttons = None
    temp_notif = None

    # config
    base_buttons = None  # [] list of emoji to enable buttons
    mapping = {}
    tracked_keys = None  # [] list of key to follow

    disable_delay = 60
    reset_delay_on_interact = False
    delete_on_disable = False
    delete_delay_on_disable = None

    one_per_user = False # only one instance of this panel per user is allowed (Voc_Panels, Welcome_panels, etc)
    one_per_user_global = False # only one instance with this bool set to true is allowed per user (Bank_panel, Inventory_Panel, Base_tool_panel)

    def get_emoji(self, name):
        return str_to_emoji(f':{name}:', self.module)

    @classmethod
    async def create(cls, channel, user, module):
        """Créer un panel dans le channel fournis en paramètre et authorise seulement l'utilisateur 
        passé en paramètre a intéragir avec, le module est nécéssaire pour le bon fonctionnement"""
        panel = cls()
        await panel.init(channel, user, module)
        return panel

    async def check_unicity(self):
        """if one_per_user is True ==> Check if the panel is unique, raise exception if not"""
        # check global first
        if self.one_per_user_global:
            for panel in self.module.all_panels:
                if panel.one_per_user_global and (panel.user == self.user):
                    await panel.disable(delete=True)

        # then check normal
        if self.one_per_user:
            for panel in self.module.all_panels:
                if isinstance(panel,self.__class__):
                    if panel.user == self.user:
                        await panel.disable(delete=True)


    async def render(self):
        # TODO: if needed make this method follow the order of the active_buttons list, actually not the case
        """Affiche le panel, ne fais rien si tout est déjà bon, ajouter les boutons et modifie l'embed au besoins"""
        self.is_rendering = True
        old_embed = self.message.embeds[0]
        new_embed = self.embed()
        if self.temp_notif is not None:
            # emoji = 'https://cdn.discordapp.com/emojis/737084672936509452.png'
            new_embed.set_footer(text=self.temp_notif) # icon_url=emoji
            self.temp_notif = None

        # message modification if needed
        if old_embed.to_dict() != new_embed.to_dict():
            await self.module.edit_message(self.message, embed=new_embed)

        if self.is_disable:
            await self.module.shared_clear_reactions(self.message)
        elif self.active_buttons is None:
            self.active_buttons = []
            for emoji in self.base_buttons:
                await self.module.shared_add_reaction(self.message, str_to_emoji(emoji, self.module))
                self.active_buttons.append(emoji)
        self.is_rendering = False

    async def add_buttons(self, *emojis):
        for emoji in emojis:
            if emoji not in self.active_buttons:
                await self.module.shared_add_reaction(self.message, str_to_emoji(emoji, self.module))
                self.active_buttons.append(emoji)

    async def remove_buttons(self, *emojis):
        channel_id = self.message.channel.id
        channel = self.module.get_channel(channel_id)
        # await channel.fetch_message(self.message.id)
        updated_message = await self.module.fetch_channel_message(channel, self.message.id)
        for emoji in emojis:
            if emoji in self.active_buttons:
                d_emoji = str_to_emoji(emoji, self.module)
                for reaction in updated_message.reactions:
                    if reaction.emoji == d_emoji:
                        await self.module.shared_clear_reaction(reaction)
                        self.active_buttons.remove(emoji)

    async def remove_all_buttons(self):
        await self.module.shared_clear_reactions(self.message)
        self.active_buttons.clear()

    async def disable(self, delete=False, delay=None):
        """Disable the panel and rerender it"""
        if not self.is_disable:
            self.is_disable = True
            if delete:
                if delay is not None:
                    await self.render()
                await self.module.shared_delete_message(self.message, delay=delay)
            else:
                await self.render()
            await self.on_disable()

    async def init(self, channel, user, module):
        """Initialise the panel"""

        self.user = user
        self.module = module

        await self.check_unicity()

        self.user_values = {}
        if self.tracked_keys is not None:
            db_user = self.module.api.db_user(user)
            for key in self.tracked_keys:
                self.user_values[key] = getattr(db_user, key)

        self.message = await self.module.send(channel, content=self.user.mention, embed=self.embed())
        module.panels.append(self)
        await self.render()
        self.module.loop.create_task(self.auto_disable_loop())

    async def delete(self, delay=None):
        """Disable the panel and delete with/out delay"""
        await self.module.shared_delete_message(self.message, delay=delay)
        self.is_disable = True

    def get(self, key):  # self.get_user('money') ==> money en directe ! (toujours à jours)
        """Return a key from the user"""
        return self.user_values[key]

    async def use(self, user, emoji):
        self.last_use = time.time()
        # await self.use(user,emoji)

    async def auto_disable_loop(self):
        if self.disable_delay is not None:
            self.last_use = time.time()
            if self.reset_delay_on_interact:
                while True:
                    await asyncio.sleep(1)
                    if time.time() > (self.last_use + self.disable_delay):
                        if not self.is_disable:
                            await self.auto_disable()
                            await self.disable(delete=self.delete_on_disable, delay=self.delete_delay_on_disable)
                        return
            else:
                await asyncio.sleep(self.disable_delay)
                if not self.is_disable:
                    await self.auto_disable()
                    await self.disable(delete=self.delete_on_disable, delay=self.delete_delay_on_disable)

    async def _input_handling(self, msg):
        message_content = narr('panel.go_back_after_input').format(panel_url=self.message.jump_url)
        go_back_msg = await self.module.send(self.message.channel, embed=discord.Embed(description=message_content))
        await self.module.shared_delete_message(go_back_msg,delay=5)
        await self.input_handling(msg)

    def embed(self):
        """Method to overide, generate the embed to display"""
        if True:
            raise Exception('This method need to be overwriten')
        return discord.Embed()

    async def on_disable(self):
        """Method to overide if needed, called when the panel is disabled (also call by auto_disable)"""
        pass

    async def auto_disable(self):
        """Method to overide if needed, called when the panel is auto disabled because of too long time or innactivity"""
        pass

    async def input_handling(self, msg):
        """Method to overdide if needed, called when a waiting input is catch"""
        pass

    async def user_updated(self, keys):
        """Method to overide if needed, called when one of the tracked_keys is modified via the API"""
        pass
