import asyncio
import time
import discord
from datetime import datetime, timedelta

from utility.loader import conf, narr
from bases.module_base import Module
from modules.basic.commands.me_command import MeCommand
from modules.basic.commands.inv_command import InvCommand
from modules.basic.commands.give_command import GiveCommand
from modules.basic.commands.stats_command import StatsCommand
from modules.basic.commands.claim_command import ClaimCommand
from modules.basic.commands.bank_command import BankCommand
from modules.basic.commands.setchapter_command import SetchapterCommand
from modules.basic.commands.help_command import HelpCommand
from utility.emoji import str_to_emoji

MESSAGE_XP = 1  # can be optain every MESSAGE_DT
VOC_XP = 10  # can be optain every VOC_DT
MESSAGE_DT = 3
VOC_DT = 60
ENERGY_DT = 900 # 15 min (to adapt if every players are full energy all the time or other extreme)
BANK_TAX_TIME = timedelta(hours=12, minutes=0)


class BasicModule(Module):
    message_cache = {}
    voc_cache = {}

    async def _on_ready(self):
        # basics commands
        self.add_command(HelpCommand)
        self.add_command(MeCommand)
        self.add_command(InvCommand)
        self.add_command(BankCommand)
        self.add_command(ClaimCommand)
        self.add_command(StatsCommand)
        
        # privilege commands
        self.add_command(SetchapterCommand)
        self.add_command(GiveCommand)

        self.loop.create_task(self.voc_xp_loop())
        self.loop.create_task(self.message_xp_loop())
        self.loop.create_task(self.voc_loop())
        self.loop.create_task(self.energy_loop())
        self.loop.create_task(self.bank_tax_loop())
        await self.send_rules()
        print("Basic run")

    @property
    def next_energy_dt(self):
        """Return how much second left before next energy_dt"""
        now = datetime.now()
        next_hour = (59-now.minute) * 60 + (60-now.second)
        return next_hour%ENERGY_DT


    @property
    def next_bank_tax_dt(self):
        """Return how much second left before next bank_tax_dt"""
        now = timedelta(hours=datetime.now().hour, minutes=datetime.now().minute, seconds=datetime.now().second)
        time_left = BANK_TAX_TIME - now
        if time_left.total_seconds() < 0:
            time_left += timedelta(days=1)
        return int(time_left.total_seconds())

    @property
    def rules_channel(self):
        return self.get_channel(conf('rules_channel'))

    @property
    def rules_embed(self):
        embed = discord.Embed(
            title=narr('rule.title'),
            colour=discord.Colour.blurple(),
            description=narr('rule.desc')
        )
        cpt = 0
        rules_desc = ""
        for idx, rule in narr('rules').items():
            cpt += 1
            rules_desc += f"**{idx}** : {rule}\n"
            if cpt >= 6:
                embed.add_field(name='_',value=rules_desc, inline=False)
                rules_desc = ""
                cpt = 0
        if rules_desc != "":
            embed.add_field(name='_',value=rules_desc, inline=False) # name=narr('rule.field_desc')

        return embed

    async def send_rules(self):
        await self.shared_purge_channel(self.rules_channel)
        # await self.send(self.rules_channel, embed=self.rules_embed)
        header_embed = discord.Embed(title=narr('rule.title'), colour=discord.Colour.blurple(), description=narr('rule.desc'))
        await self.send(self.rules_channel, embed=header_embed)
        for idx, rule in narr('rules').items():
            rules_desc = f"**{idx}**  ‣  {rule}"
            rule_embed = discord.Embed(colour=discord.Colour.blurple(), description=rules_desc)
            await self.send(self.rules_channel, embed=rule_embed)



    async def voc_xp_loop(self):
        """Give xp and vocal_time for each player active in voc every voc_dt"""
        while True:
            await asyncio.sleep(VOC_DT)
            if len(self.voc_cache) > 0:
                await self.api.voc_actives(VOC_DT, VOC_XP, self.voc_cache)
                self.voc_cache.clear()

    async def message_xp_loop(self):
        """Give xp and message_sent for each player who sent a message in the last message_dt"""
        while True:
            await asyncio.sleep(MESSAGE_DT)
            if len(self.message_cache) > 0:
                message_cache = self.message_cache.copy()
                self.message_cache.clear()
                await self.api.message_actives(MESSAGE_DT, MESSAGE_XP, message_cache)

    async def voc_loop(self):
        """Allow to calculate exactly how much time players pass in voc without the dt problem"""
        while True:
            await asyncio.sleep(1)
            users = [user for user, voc_data in self.main_bot.in_voc.items()
                     if voc_data['active']]
            for user in users:  # active members
                if user not in self.voc_cache:
                    self.voc_cache[user] = 1
                else:
                    self.voc_cache[user] += 1

    async def _on_message(self, message):
        user = message.author
        if user not in self.message_cache:
            self.message_cache[user] = []
        self.message_cache[user].append(message)

    async def energy_loop(self):
        while True:
            await asyncio.sleep(self.next_energy_dt)
            await self.api.energy_loop()
            await asyncio.sleep(5) # security purpose (in case 'self.api.energy_loop' take less than 1 second (very probable))

    async def bank_tax_loop(self):
        while True:
            await asyncio.sleep(self.next_bank_tax_dt)
            await self.api.bank_tax_loop()
            await asyncio.sleep(5) # security purpose (in case 'self.api.bank_tax_loop' take less than 1 second (very probable))


    async def _just_join(self,user,inviter,first_join):
        if not first_join:
            level_roles_id = conf('level_ranks')
            roles_to_add = []
            db_user = self.api.db_user(user)
            
            for level in range(db_user.level):
                level_role_id = level_roles_id.get(level,None)
                if level_role_id is not None:
                    roles_to_add.append(self.guild.get_role(level_role_id))
                
            if len(roles_to_add) > 0:
                await self.shared_add_user_roles(user,*roles_to_add)