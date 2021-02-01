import discord
import asyncio
import random
from objects.item import Stack
from modules.activity.panels.tool_panel import ToolPanel
from utility.loader import narr

class AnimalHuntingPanel(ToolPanel):
    mapping = {
        '🐾':{'callback':'on_hunt','action':''},
    }
    base_buttons = ['🐾',]

    def tool_embed(self):
        return discord.Embed(
            title = narr('activity.animalhunting.game_title').format(name=self.user.display_name),
            colour = discord.Colour.blurple(),
            description = narr('activity.animalhunting.game_desc')
        )

    async def on_hunt(self):
        for _ in range(self.uses):
            self.add_loot()
        await self.end_the_game()