import discord
import asyncio
import random
from objects.item import Stack
from bases.panel_base import Panel
from utility.loader import narr
from api.api import NotEnoughtMoneyException

class BaseToolPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = True
    one_per_user_global = True
    
    tracked_keys = ['money', 'rank']
    mapping = {
        '✔️': {'callback': 'accept', 'action': ''},
        '❌': {'callback': 'refuse', 'action': ''},
    }
    base_buttons = ['✔️', '❌']

    state = 'confirmation'

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    async def user_updated(self, keys):
        await self.render()

    @property
    def base_tool(self):
        return self.get('rank').gain_tools[0]

    @property
    def base_tool_price(self):
        return int(self.base_tool.buy_price / 3)

    def confirmation_embed(self):
        return discord.Embed(
            title=narr('rank.base_tool_panel.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('rank.base_tool_panel.desc').format(
                tool_name=self.base_tool.display_name,
                value=self.base_tool_price,
                emoji=self.get_emoji('money'),
            )
        )

    def payed_embed(self):
        return discord.Embed(
            title=narr('rank.base_tool_panel.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('rank.base_tool_panel.payed_desc')
        )

    """ Buttons """

    async def accept(self):
        try:
            self.state = 'payed'
            await self.module.api.buy_base_tool(self.user)
            await self.disable()

            db_user = self.module.api.db_user(self.user)
            await self.module.trigger_hook('buy_base_tool', self.user, db_user.rank.index)
        except NotEnoughtMoneyException as e:
            self.state = 'confirmation'
            self.temp_notif = narr('rank.base_tool_panel.notifications.no_money').format(value=e.missing,currency=narr('currency'))
            await self.render()

    async def refuse(self):
        await self.disable()
