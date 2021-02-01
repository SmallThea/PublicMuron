import asyncio
import time
import discord

from bases.module_base import Module
from modules.voc.panels.voc_creation_panel import VocCreationPanel
from utility.loader import conf, narr

DELETE_DELAY = 120
SEPARATOR = '┃'


class VocModule(Module):
    timestamp_cache = {}
    panel_cache = {}
    tables = []  # list of TableChannel
    delete_delay = DELETE_DELAY

    @property
    def text_channel(self):
        return self.get_channel(conf('voc.text_channel'))

    @property
    def voice_channel(self):
        return self.get_channel(conf('voc.voice_channel'))

    @property
    def category_channel(self):
        return self.get_channel(conf('voc.category_channel'))

    async def _on_ready(self):
        await self.clean_stuff()
        print("Voc run")

    async def clean_stuff(self):
        for channel in self.category_channel.voice_channels:
            if channel != self.voice_channel:
                await self.shared_delete_channel(channel)

        overwrites = self.voice_channel.overwrites
        for user in overwrites.copy():
            if isinstance(user, discord.member.Member):
                del overwrites[user]
        await self.shared_edit_channel(self.voice_channel, overwrites=overwrites)

        await self.shared_purge_channel(self.text_channel)
        embed = discord.Embed(
            title=narr('voc.introduction.title'),
            colour=discord.Colour.blurple(),
            description=narr('voc.introduction.desc').format(delay=self.delete_delay,voice_channel=self.voice_channel.mention,voice_invitation=conf('voc.voice_invitation')),
        )
        await self.send(self.text_channel, embed=embed)

    def get_table_from_user(self, user):
        for table in self.tables[:]:
            if table.owner == user:
                return table

    def get_table_from_channel(self, channel): # table_channel
        for table in self.tables[:]:
            if table.voice_channel == channel:
                return table
        return None

    async def _on_guild_channel_delete(self, channel):
        table = self.get_table_from_channel(channel)
        if table is not None:
            await table.on_delete()
            # self.timestamp_cache.pop(channel.id, None)

    async def _on_guild_channel_update(self, before, after):
        table = self.get_table_from_channel(after)
        if table is not None:
            kwargs = {
                'name': None,
                'user_limit': None,
                'overwrites':None,
            }

            if before.name != after.name:
                prefix = table.table.prefix
                if len(prefix) > 1:
                    raise Exception(
                        f"len(table.prefix) > 1, use this '{prefix[0]}'")

                if after.name[:2] != f'{prefix}{SEPARATOR}':
                    kwargs['name'] = f'{prefix}{SEPARATOR}{after.name}'[:100]

            if before.user_limit != after.user_limit:
                table_limit = table.table.max_size
                if table_limit is not None:
                    if (after.user_limit == 0) or (after.user_limit > table_limit):
                        kwargs['user_limit'] = table_limit

            if after.overwrites != table.base_permissions:
                kwargs['overwrites'] = table.base_permissions
                

            kwargs = {key: value for key,
                      value in kwargs.items() if value is not None}
            if len(kwargs) > 0:
                await self.shared_edit_channel(after, **kwargs)

    async def _on_voice_state_update(self, user, before, after):
        before = before.channel
        after = after.channel
        swap = (before != after)

        # triger the 'leave' event on panel if needed
        if swap and (before == self.voice_channel):
            panel = self.panel_cache.get(user.id, None)
            if panel is not None:
                if not panel.is_disable:
                    await panel.leave()
                del self.panel_cache[user.id]

        # create panel if user don't have table
        if swap and (after == self.voice_channel):
            if self.panel_cache.get(user.id, None) is None:
                table = self.get_table_from_user(user)
                if table is None:
                    self.panel_cache[user.id] = await VocCreationPanel.create(self.text_channel, user, self)
                else:
                    pass  # join while already a table, just do nothing

        # refresh the 'last_activity' for handling auto_delete of table with delay
        if swap and (after is not None):
            table = self.get_table_from_channel(after)
            if table is not None:
                if len(after.members) == 1:
                    await table.pass_no_empty()

        # trigger the timer for deleting the channel when left
        if swap and (before is not None):
            table = self.get_table_from_channel(before)
            if (table is not None) and (len(before.members) == 0):
                await table.pass_empty()
