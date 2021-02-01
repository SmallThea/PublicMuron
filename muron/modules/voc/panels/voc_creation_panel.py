import discord
import asyncio
import random

from utility.loader import conf, narr
from objects.item import Stack
from objects.table import Table, TableChannel, NoRoleException, NoMoneyException
from bases.panel_base import Panel

# TODO: buff de table
# TODO: conditions de tables
# TODO: objet table avec tout ce qu'il faut


class VocCreationPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = False
    delete_on_disable = True
    delete_delay_on_disable = 20
    one_per_user = True

    tracked_keys = ['money']
    mapping = {
        '🔼': {'callback': 'go_up'},
        '🟩': {'callback': 'accept'},
        '🟥': {'callback': 'refuse'},
        '🔽': {'callback': 'go_down'},
    }
    base_buttons = ['🔼', '🟩', '🟥', '🔽']
    table_list = [table() for table in Table.tables()]

    cursor = 0  # used for table selection
    state = 'selection'  # creating, to_slow, leave, refuse

    finished = False

    timeout_time = 120  # time before kick you for too long
    kick_time = 120  # for how much time you should be kick from the voc
    delete_delay = 15  # time before deleting finished panels

    @property
    def voice_channel(self):
        return self.module.voice_channel

    @property
    def current_table(self):
        return Table.by_index(self.cursor)

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def selection_embed(self):
        embed = discord.Embed(
            title=narr('voc.creation.title').format(
                name=self.user.display_name),
            colour=discord.Colour.blurple(),
        )
        embed.description = f"{narr('voc.creation.desc')}\n\n{self.table_selector()}"
        table_name, table_desc = self.table_info()
        embed.add_field(name=table_name, value=table_desc, inline=False)
        return embed

    def creating_embed(self):
        return discord.Embed(
            title=narr('voc.creation.title').format(
                name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('voc.creation.creating_desc')
        )

    def to_slow_embed(self):
        return discord.Embed(
            title=narr('voc.creation.title').format(
                name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('voc.creation.to_slow_desc')
        )

    def leave_embed(self):
        return discord.Embed(
            title=narr('voc.creation.title').format(
                name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('voc.creation.leave_desc')
        )

    def refuse_embed(self):
        return discord.Embed(
            title=narr('voc.creation.title').format(
                name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('voc.creation.refuse_desc')
        )

    def table_selector(self):
        out = ''
        for table in self.table_list:
            prefix = '◆' if (table.index == self.cursor) else '◇'
            can_afford = '🟢' if table.can_afford(
                self.user, self.module) else '🔴'
            out += f'{prefix} {table.prefix}┃{table.display_name} - {can_afford}\n'
        return out

    def table_info(self):
        """Return a tuple with selected table name and desc"""
        table = self.current_table
        desc = table.description
        desc += '\n\n'
        # desc += f"{narr('price')} : {table.price}{self.get_emoji('money')}\n"
        desc += f"{narr('voc.creation.max_size')} : {table.max_size if (table.max_size is not None) else '∞'}\n"

        desc += f"{narr('voc.creation.allowed_roles')} : "
        if table.allowed_roles is not None:
            roles_names = [self.module.guild.get_role(
                role_id).mention for role_id in table.allowed_roles]
            desc += f"{', '.join(roles_names)}\n"
        else:
            desc += f"{narr('voc.creation.everyone')}\n"

        if table.stats_modifier is not None:
            title = f"\n{narr('voc.creation.buff_title')} : "
            add_stats = "\n".join([f"   ▹{narr(f'stats.{stat}')} +{value}" for stat,
                                   value in table.stats_modifier.get('add', {}).items()])
            mult_stats = "\n".join([f"  ▹{narr(f'stats.{stat}')} +{value*100}%" for stat,
                                    value in table.stats_modifier.get('mult', {}).items()])
            desc += f"{title}\n{add_stats}\n{mult_stats}\n"
        return (f"{table.prefix}┃{table.display_name} [ {table.price}{self.get_emoji('money')} ]", desc)

    async def go_up(self):
        self.cursor = 0 if ((self.cursor-1) < 0) else (self.cursor - 1)
        await self.render()

    async def go_down(self):
        self.cursor = (self.cursor+1) % len(self.table_list)
        await self.render()

    async def accept(self):
        table = self.current_table
        try:
            table.can_afford_err(self.user, self.module)
        except NoRoleException:
            self.temp_notif = narr('voc.creation.no_role_err')
            await self.render()
        except NoMoneyException:
            self.temp_notif = narr('voc.creation.no_money_err')
            await self.render()
        else:
            self.state = 'creating'
            await self.disable(delete=True, delay=20)
            await self.good_end()

    async def refuse(self):
        self.state = 'refuse'
        await self.disable(delete=True, delay=20)
        await self.bad_end()

    async def leave(self):
        self.state = 'leave'
        await self.disable(delete=True, delay=20)
        await self.bad_end()

    async def good_end(self):
        table = self.current_table
        await self.module.api.add_money(self.user, -table.price)
        table_channel = await TableChannel.create(table.index, self.user, self.module)
        self.module.tables.append(table_channel)

    async def bad_end(self):
        if self.user in self.voice_channel.members:
            await self.module.shared_move_user(self.user, None)
        await self.deny_create()
        self.module.loop.create_task(self.allow_create())

    async def auto_disable(self):
        """Called automaticaly when user take to much time"""
        self.state = 'to_slow'
        await self.bad_end()

    async def deny_create(self):
        overwrites = self.voice_channel.overwrites
        user_perm = discord.PermissionOverwrite(connect=False)
        overwrites[self.user] = user_perm
        await self.module.shared_edit_channel(self.voice_channel, overwrites=overwrites)

    async def allow_create(self):
        """Wait for the delay then allop again to join"""
        await asyncio.sleep(self.kick_time)
        overwrites = self.voice_channel.overwrites
        perm = overwrites.pop(self.user, None)
        if perm is not None:
            await self.module.shared_edit_channel(self.voice_channel, overwrites=overwrites)
