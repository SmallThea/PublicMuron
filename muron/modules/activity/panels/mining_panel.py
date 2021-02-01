import discord
import asyncio
import random
from objects.item import Stack
from modules.activity.panels.tool_panel import ToolPanel
from utility.loader import narr

class MiningPanel(ToolPanel):
    mapping = {
        '⛏️':{'callback':'on_mine','action':""},
        '◀️':{'callback':'go_left','action':""},
        '▶️':{'callback':'go_right','action':""},
        '🔼':{'callback':'go_up','action':""},
        '🔽':{'callback':'go_down','action':""},
    }
    base_buttons = ['⛏️', '◀️', '▶️', '🔼', '🔽']

    usage = 0
    no_cursor = False
    _vein = None
    _coord = None

    X_MAX = 13
    Y_MAX = 6

    @property
    def vein(self):
        if self._vein is None:
            self._vein = [[None for x in range(self.Y_MAX)] for y in range(self.X_MAX)]
        return self._vein
    
    @property
    def coord(self):
        if self._coord is None:
            self._coord = {
                'x':random.randint(0,self.X_MAX-1),
                'y':random.randint(0,self.Y_MAX-1),
                }
        return self._coord

    @property
    def usage_remaining(self):
        return self.uses - self.usage

    def tool_embed(self):
        return discord.Embed(
            title = narr('activity.mining.game_title').format(name=self.user.display_name),
            colour = discord.Colour.blurple(),
            description = f"{narr('activity.mining.game_desc')}\n\n{self.game_screen}"
        )

    @property
    def game_screen(self):
        out = ""
        for y in range(self.Y_MAX):
            line = ''
            for x in range(self.X_MAX):
                ore = self.vein[x][y]
                if x == self.coord['x'] and y == self.coord['y']:
                    if self.no_cursor:
                        line += self.get_emoji(ore.item.emoji) # str_to_emoji(ore.item.emoji,self.module)
                    elif ore is not None:
                        line += '🟥'
                    else:
                        line += '🟩'
                elif ore is not None:
                    line += self.get_emoji(ore.item.emoji) # str_to_emoji(ore.item.emoji,self.module)
                else:
                    line += '⬛'
            out = f"{line}\n{out}"
        if self.usage_remaining > 0:
            out += "\n"
            out += narr('activity.mining.usage_remaining').format(value=self.usage_remaining)
        return out

    async def go_right(self):
        self.no_cursor = False
        if self.coord['x'] < self.X_MAX-1:
            self.coord['x'] += 1
            await self.render()

    async def go_left(self):
        self.no_cursor = False
        if self.coord['x'] > 0:
            self.coord['x'] -= 1
            await self.render()

    async def go_up(self):
        self.no_cursor = False
        if self.coord['y'] < self.Y_MAX-1:
            self.coord['y'] += 1
            await self.render()

    async def go_down(self):
        self.no_cursor = False
        if self.coord['y'] > 0:
            self.coord['y'] -= 1
            await self.render()

    async def on_mine(self):
        to_mine = self.vein[self.coord['x']][self.coord['y']]
        if to_mine is None:
            self.no_cursor = True
            loot = self.add_loot()
            self.usage += 1
            self.vein[self.coord['x']][self.coord['y']] = loot
            await self.render()
        if self.usage_remaining <= 0:
            self.no_cursor = True
            await self.end_the_game()