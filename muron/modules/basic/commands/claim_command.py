import discord
import asyncio
import datetime
from marshmallow import Schema,fields,validate

from utility.loader import narr, conf
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command,UserField
from objects.item import Stack
from objects.rule import Rule

from api.api import InventoryFullException, NotEnoughtEnergyException

"""
Commande temporaire qui permet en échange de 3 d'énergie de gagner une récompense en fonction de notre rang
(récompense de donjon)

==> pierre d'amélioration de stuff / parchemin de craft d'outils 
"""

class ClaimSchemas(Schema):
    pass

class ClaimCommand(Command):
    name = 'claim'
    schemas = ClaimSchemas
    args_description = {}
    minArgs = 0

    async def run(self):
        try:
            stacks = await self.module.api.claim_loot(self.sender)
            await self.module.send(self.channel, self.sender.mention, embed=self.loot_embed(stacks))

            #hook
            await self.module.trigger_hook('claim_loots',self.sender,stacks)
        except NotEnoughtEnergyException as e:
            await self.module.send(self.channel, self.sender.mention, embed=self.no_energy_embed(e.missing))
        except Exception as e:
            raise e

    def loot_embed(self,stacks):
        loot_str = ""
        for stack in stacks:
            loot_str += f"- {stack.to_str(self.module)}\n"
        return discord.Embed(
            title=narr('claim_command.title').format(name=self.sender.display_name),
            colour=discord.Colour.blurple(),
            description=f"{narr('claim_command.loot_desc')}\n\n{loot_str}"
        )

    def no_energy_embed(self,missing):
        return discord.Embed(
            title=narr('claim_command.title').format(name=self.sender.display_name),
            colour=discord.Colour.blurple(),
            description=narr('claim_command.no_energy_desc').format(missing=missing)
        )