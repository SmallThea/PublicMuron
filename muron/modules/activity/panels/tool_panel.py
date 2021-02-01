import asyncio
import discord
import random

from objects.item import Item, Stack
from utility.loader import narr
from utility.other import apply_luck
from bases.panel_base import Panel
from utility.emoji import emoji_bar

class ToolPanel(Panel):

    disable_delay = 3600 # 1h
    reset_delay_on_interact = False
    delete_on_disable = False

    tracked_keys = ['tool', 'energy', 'energy_max','stats']
    _loots = None  # list of Stack
    tool_used = None

    reach_to_slow = False
    gone_wrong = False

    #TODO: réécrire la méthode create qui va prendre en paramètre l'outil utilisé (le stack)
    # stocker cette outil pour l'utilisation du panel
    # ajouter dans tracked_keys l'équipement et non le tool qui ne se fait jamais update
    # quand on a une modification sur l'équipement vérifié si le tool a changé si oui alors anulé le panel
    # pareil sur l'énergie si elle passe sous le 1 anuler le panel

    @classmethod
    async def create(cls, channel, user, module, tool_used):
        panel = cls()
        panel.tool_used = tool_used
        await panel.init(channel, user, module)
        return panel
    
    async def user_updated(self, keys):
        if 'tool' in keys:
            last = self.tool_used
            new = self.get('tool')
            if new is None:
                is_same_tool = False
            else:
                bools = [
                    last.item == new.item,
                    last.upgrade_level == new.upgrade_level,
                    last.stats_repartition == new.stats_repartition, # not sure if dicts can be compares
                    last.durability == (new.durability + 1),
                ]
                is_same_tool = (len([e for e in bools if not e]) == 0) # check if all elements are true
                
            if is_same_tool:
                self.tool_used = self.get('tool')
            else:
                self.gone_wrong = True
                await self.disable()
        elif 'energy' in keys:
            if self.get('energy') <= 0:
                self.gone_wrong = True
                await self.disable()


    async def cancel_panel(self):
        pass

    @property
    def collect_field_name(self):
        try:
            return narr(f'activity.{self.module.name}.collect_field_name')
        except:
            return narr('activity.default.collect_field_name')

    @property
    def too_slow_field_name(self):
        try:
            return narr(f'activity.{self.module.name}.too_slow_field_name')
        except:
            return narr('activity.default.too_slow_field_name')

    @property
    def too_slow_content(self):
        try:
            return narr(f'activity.{self.module.name}.too_slow_content')
        except:
            return narr('activity.default.too_slow_content')

    @property
    def tool_break_content(self):
        try:
            return narr(f'activity.{self.module.name}.tool_break_content')
        except:
            return narr('activity.default.tool_break_content')

    @property
    def loots(self):
        if self._loots is None:
            self._loots = []
        return self._loots

    @property
    def uses(self):
        return self.get('tool').item.uses

    def tool_embed(self):
        """Method to overide by tool panels childs"""
        if True:
            raise Exception('This method need to be overwriten')
        return discord.Embed()

    def embed(self):
        if self.gone_wrong:
            return self.gone_wrong_embed()
        elif self.reach_to_slow:
            return self.too_slow_embed()
        else:
            embed = self.tool_embed()
            if self.is_disable:  # game finished
                for name, desc in self.end_fields():
                    embed.add_field(name=name, value=desc, inline=False)
            return embed

    def end_fields(self):
        fields = []
        field_name = self.collect_field_name
        content = '\n'.join([stack.to_str(self.module)
                             for stack in self.loots])
        fields.append((field_name, content))

        field_name = narr('recap')
        content = ''
        # if (self.tool_used.durability == 0):
        #     content += '❗ ' + self.tool_break_content.format(tool_name=self.tool_used.display_name) + "\n"
        # else:

        actual_d = self.tool_used.durability
        max_d = self.tool_used.item.max_durability
        content += f"{narr('durability')} : {emoji_bar(8,actual_d/max_d,'🟦','⬛',self.module)}  {actual_d} / {max_d}\n"

        actual_e = self.get('energy')
        max_e = self.get('energy_max')
        if actual_e > 0:
            content += f"{narr('energy')} : {emoji_bar(8,actual_e/max_e,'🟨','⬛',self.module)}  {actual_e} / {max_e}\n"
        else:
            content += f"❗ {narr('activity.no_energy')}┃{actual_e} / {max_e}\n"

        content += f"{narr('xp')} : +{self.module.activity_xp}"

        fields.append((field_name, content))
        return fields

    def too_slow_embed(self):
        return discord.Embed(
            title=self.too_slow_field_name,
            colour=discord.Colour.blurple(),
            description=self.too_slow_content
        )

    def gone_wrong_embed(self):
        return discord.Embed(
            title=narr('activity.default.gone_wrong_field_name'),
            colour=discord.Colour.blurple(),
            description=narr('activity.default.gone_wrong_content')
        )

    def add_loot(self):
        loot = self.random_loot()
        display_loot = loot.copy()
        for l in self.loots:
            if l.item.name == loot.item.name:
                loot = l.merge(loot)
                if loot is None:
                    break
        if loot is not None:
            self.loots.append(loot)
        return display_loot

    def random_loot(self):
        loot_weight = {item_name: Item.by_name(item_name).frequency for item_name in self.tool_used.item.loots}
        
        luck = self.get('stats')['luck']
        apply_luck(loot_weight, luck)

        summ = sum([weight for weight in loot_weight.values()])
        offset = random.random()*summ
        for item_name, weight in loot_weight.items():
            if offset < weight:
                return Stack(item_name, 1)
            offset -= weight

    async def end_the_game(self):
        # used because after this operation tool can be none
        await self.module.api.tool_loot(self.user, self.loots, self.module.activity_xp)
        await self.module.trigger_hook('activity_loot',self.user,self.loots)
        await self.disable()

    async def auto_disable(self):  # est appellé avant le disable (qui va render)
        self.reach_to_slow = True
        await self.render()
