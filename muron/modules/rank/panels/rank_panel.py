import discord
import asyncio
import random
from objects.item import Stack
from bases.panel_base import Panel
from utility.loader import narr

YES = '🟢'
NO = '🔴'


class RankPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = True
    one_per_user_global = True

    mapping = {
        '⬆️': {'callback': 'up', 'action': ''},
        '⬇️': {'callback': 'down', 'action': ''},
        '🟥': {'callback': 'close', 'action': ''},
        '✔️': {'callback': 'accept', 'action': ''},
        '❌': {'callback': 'refuse', 'action': ''},
    }
    base_buttons = ['⬆️', '⬇️','🟥']
    tracked_keys = ['level', 'money', 'rank']

    state = 'rank'  # up_validation , down_validation,

    async def user_updated(self, keys):
        await self.render()

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def rank_embed(self):
        embed = discord.Embed(
            title=narr('rank.panel.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('rank.panel.desc')
        )
        actual_rank = self.get('rank')
        pre_rank = actual_rank.pre_rank
        next_rank = actual_rank.next_rank
        embed.add_field(name=f"{narr('rank.panel.actual_rank')}",value=self.rank_field(actual_rank), inline=False)
        if pre_rank is not None:
            embed.add_field(name=f"{narr('rank.panel.pre_rank')}",value=self.rank_field(pre_rank), inline=False)
        else:
            embed.add_field(name=f"{narr('rank.panel.pre_rank')}", value=narr('rank.panel.no_pre_rank'), inline=True)
        if next_rank is not None:
            embed.add_field(name=f"{narr('rank.panel.next_rank')}",value=self.rank_field(next_rank, goal=True), inline=False)
        else:
            embed.add_field(name=f"{narr('rank.panel.next_rank')}", value=narr('rank.panel.no_next_rank'), inline=True)
        return embed

    def rank_field(self, rank, goal=False):
        out = ""
        out += f"{rank.role(self.module).mention} : *{rank.description}*\n\n"
        out += f"- {narr('rank.panel.needed_level')} : {rank.needed_level} {goal and (self.get('level') >= rank.needed_level and YES or NO) or ''}\n"
        out += f"- {narr('rank.panel.price')} : {rank.price} {self.get_emoji('money')} {goal and (self.get('money') >= rank.price and YES or NO) or ''}\n"
        out += f"- {narr('rank.panel.tax')} : {rank.tax} {self.get_emoji('money')}\n"
        out += f"- {narr('rank.panel.base_tool')} : {rank.gain_tools[0].display_name}\n"
        out += f"- {narr('rank.panel.unlocked_tools')} : {', '.join([item.display_name for item in rank.gain_tools]) }\n"
        return out

    def up_validation_embed(self):
        rank = self.get('rank').next_rank
        return discord.Embed(
            title=narr('rank.panel.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('rank.panel.next_validation').format(rank_name=rank.display_name, price=rank.price, tax=rank.tax,
                                                                  money_emoji=self.get_emoji('money'), tool_names=' ,'.join([item.display_name for item in rank.gain_tools]))
        )

    def down_validation_embed(self):
        rank = self.get('rank').pre_rank
        return discord.Embed(
            title=narr('rank.panel.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('rank.panel.pre_validation').format(rank_name=rank.display_name, tax=rank.tax, money_emoji=self.get_emoji(
                'money'), tool_names=' ,'.join([item.display_name for item in self.get('rank').gain_tools]))
        )

    """ Buttons """

    async def close(self):
        await self.disable()

    async def up(self):
        next_rank = self.get('rank').next_rank
        if next_rank is not None:
            if (self.get('level') >= next_rank.needed_level) and (self.get('money') >= next_rank.price):
                await self.remove_buttons('⬆️', '⬇️','🟥')
                await self.add_buttons('✔️', '❌')
                self.state = 'up_validation'
            else:
                self.temp_notif = narr('rank.panel.notifications.no_requirement')
        else:
            self.temp_notif = narr('rank.panel.notifications.cant')
        await self.render()

    async def down(self):
        pre_rank = self.get('rank').pre_rank
        if pre_rank is not None:
            await self.remove_buttons('⬆️', '⬇️','🟥')
            await self.add_buttons('✔️', '❌')
            self.state = 'down_validation'
        else:
            self.temp_notif = narr('rank.panel.notifications.cant')
        await self.render()

    async def accept(self):
        state = self.state
        self.state = 'rank'
        await self.remove_buttons('✔️', '❌')
        await self.add_buttons('⬆️', '⬇️','🟥')
        if state == 'up_validation':
            next_rank = self.get('rank').next_rank
            if (next_rank is not None) and (self.get('level') >= next_rank.needed_level) and (self.get('money') >= next_rank.price):
                self.temp_notif = narr('rank.panel.notifications.rank_up')
                await self.module.api.rank_up(self.user)
                
            else:
                self.render()  # should not happen but in case
        elif state == 'down_validation':
            pre_rank = self.get('rank').pre_rank
            if pre_rank is not None:
                await self.module.api.rank_down(self.user)
            else:
                await self.render()

    async def refuse(self):
        self.state = 'rank'
        await self.remove_buttons('✔️', '❌')
        await self.add_buttons('⬆️', '⬇️','🟥')
        await self.render()
