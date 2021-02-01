import asyncio
import time
import discord

from utility.loader import conf, narr
from bases.module_base import Module
from modules.rank.commands.rank_command import RankCommand
from modules.rank.commands.base_tool_command import BaseToolCommand
from modules.rank.panels.rank_panel import RankPanel
from objects.rank import Rank, RANK_LIST
from datetime import timedelta, datetime


class RankModule(Module):
    # timedelta(hours=11,minutes=00)
    update_tax_time = timedelta(hours=11, minutes=00)
    tax_time = timedelta(hours=13, minutes=00)
    info_message = None

    async def _on_ready(self):
        self.add_command(RankCommand)
        self.add_command(BaseToolCommand)
        await self.shared_purge_channel(self.info_channel)
        await self.update_taxes()
        self.loop.create_task(self.tax_loop())
        self.loop.create_task(self.update_tax_loop())
        print("Rank run")

    @property
    def info_channel(self):
        return self.get_channel(conf('rank.info_channel'))

    @property
    def now(self):
        return timedelta(hours=datetime.now().hour, minutes=datetime.now().minute, seconds=datetime.now().second)

    @property
    def info_embed(self):
        embed = discord.Embed(
            title=narr('rank.info.title'),
            colour=discord.Colour.blurple(),
            description=narr('rank.info.desc')
        )
        money_emoji = self.get_emoji('money')
        for _rank in RANK_LIST:
            rank = _rank()
            description = ""
            description += f"{narr('rank.info.price')} : {rank.price}{money_emoji}\n"
            description += f"{narr('rank.info.tax')} : {rank.tax}{money_emoji}\n"
            if rank.real_proportion is not None:
                description += f"{narr('rank.info.proportion')} : {round(rank.proportion*100)}%\n"
                description += f"{narr('rank.info.real_proportion')} : {round(rank.real_proportion*100,2)}%\n"

                multiply = rank.proportion_multiply
                if multiply < 1:
                    multiply = f"-{round(1/multiply*100,2)}%"
                elif multiply >= 1:  # else
                    multiply = f"+{round((multiply-1)*100,2)}%"
                description += f"{narr('rank.info.price_modifier')} : {multiply}\n"
            embed.add_field(name=rank.display_name,
                            value=description, inline=False)

        hour_desc = f"{narr('rank.info.update_time')} : {str(self.update_tax_time)[:-3]}\n{narr('rank.info.pay_time')} : {str(self.tax_time)[:-3]}"
        embed.add_field(name=narr('rank.info.time_title'),
                        value=hour_desc, inline=False)
        return embed

    async def _just_join(self,user,inviter,first_join):
        if not first_join:
            db_user = self.api.db_user(user)
            rank_role = self.guild.get_role(db_user.rank.role_id)
            await self.shared_add_user_roles(user,rank_role)

    async def update_panels(self):
        for panel in self.panels:
            if panel.__class__ == RankPanel:
                await panel.render()  # we rerender because certain player didn't get updateded but the rank prices did, with this method the price should be actualise for every panels

    async def tax_loop(self):
        while True:
            time_left = self.tax_time-self.now
            if time_left.total_seconds() < 0:
                time_left += timedelta(days=1)
            await asyncio.sleep(time_left.total_seconds())
            await self.pay_taxes()
            await asyncio.sleep(5)

    async def pay_taxes(self):
        await self.api.tax_loop()

    async def update_tax_loop(self):
        while True:
            time_left = self.update_tax_time-self.now
            if time_left.total_seconds() < 0:
                time_left += timedelta(days=1)
            await asyncio.sleep(time_left.total_seconds())
            await self.update_taxes()
            await self.update_panels()
            await asyncio.sleep(5)

    async def update_taxes(self):
        await self.api.update_rank_prices()
        if self.info_message is None:
            self.info_message = await self.send(self.info_channel, embed=self.info_embed)
        else:
            await self.edit_message(self.info_message, embed=self.info_embed)
