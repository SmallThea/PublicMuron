import discord
import random
from bases.panel_base import Panel
from objects.item import Stack
from utility.loader import narr
from utility.emoji import emoji_bar
from api.models.user import (
    InventoryFullException, 
    NotEnoughtResourcesException, 
    MaxLevelException,
    MaxDurabilityException,
    UpgradeFailedException,
    NoRequiredRankException,
)

CURRENCY = narr('currency')
INV_WIDTH = 4

SPACE = ''.join([' ' for i in range(20)])
EQUIPMENT_TEMPLATE = """┃              {_0} {_1}              ┃
┃        {_2} {_3} {_4}      ┃
┃{_5} {_6} {_7} {_8}┃
┃        {_9} {_10} {_11}      ┃
┃                      {_12}                     ┃"""

#TODO: faire un système de page + ajouter des boutons pour avancer de pages en pages
#TODO: chaque amélioration avec des gemmes peut alors ajouter 4 slots et comme ca pas de soucis de ligne incomplètes

# raise Exception('DO THIS')

# """
# 1 ) faire la section amélioration (marteau qui s'enlève et s'ajoute si on passe sur de l'équipement)
# 2 ) state = upgrade avec chance de réussite, petite animation éventuellement etc (gif) et timing sur le render
# 3 ) 
# """

INV_BUTTONS = ['◀️', '▶️', '🔼', '🔽', '🔁', '✋🏼', '💸', '🔨', '❌'] # '🔄'


class InvPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = True
    delete_on_disable = False
    one_per_user_global = True
    
    tracked_keys = ['inventory', 'equipment','tool']
    mapping = {
        '◀️': {'callback': 'go_left', 'desc': ""},
        '▶️': {'callback': 'go_right', 'desc': ""},
        '🔼': {'callback': 'go_up', 'desc': ""},
        '🔽': {'callback': 'go_down', 'desc': ""},
        '🔁': {'callback': 'swap', 'desc': ""},
        '✋🏼': {'callback': 'use_item', 'desc': ""},
        '💸': {'callback': 'sell', 'desc': ""},
        '🔄': {'callback': 'sell_ply', 'desc': ""},
        '❌': {'callback': 'close', 'desc': ""},
        '🟩': {'callback': 'accept', 'desc': ""},
        '🟥': {'callback': 'refuse', 'desc': ""},
        '↩️': {'callback': 'go_back', 'desc': ""},
        '🔨': {'callback': 'upgrade', 'desc': ""},
        '🔧': {'callback': 'repair', 'desc': ""},
    }
    base_buttons = INV_BUTTONS

    cursor = 0
    swap_slot = None
    to_sell_stack = None # stack to sell, used by sell button
    upgrade_recap = None # dict of upgraded stats used by upgrade part
    repair_recap = None # quantity of durability restored used by repair part
    upgrade_fail_streak = 0 # consecutive fails in upgrades

    state = 'inv'
    # 'inv' => moving in inventory
    # 'drop' => ask validation for droping the item
    # 'give' => ask validation for giving the item
    # 'sell_0' => ask quantity for sell
    # 'sell_1' => ask validation for selling stuff

    @property
    def selected(self):
        return self.get('inventory')[self.cursor]

    async def user_updated(self, keys):
        await self.render()

    async def input_handling(self, msg):
        if self.state == 'sell_0':
            try:
                self.set_sell_quantity(sorted((1,int(msg),self.selected.quantity))[1])
            except:
                self.temp_notif = narr('inventory.notifications.wrong_sell_quantity')
                self.is_waiting_input = True
            else:
                self.state = 'sell_1'
                await self.remove_buttons('↩️')
                await self.add_buttons('🟩','🟥')
        await self.render()


    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def inv_embed(self):
        embed = discord.Embed(
            title=narr('inventory.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple()
        )
        equ_part = self.equipment()
        inv_part = self.inventory()
        info_part = self.infos()

        embed.add_field(name=narr('inventory.equipment_desc'),value=equ_part, inline=True)
        embed.add_field(name=narr('inventory.inventory_desc'),value=inv_part, inline=True)
        if info_part is not None:
            embed.add_field(name=info_part[0],value=info_part[1], inline=False)
        return embed

    def infos(self):
        """Generate the info about a item, return a tuple with item name and infos, None if no stack selected"""
        if self.selected is not None:
            stack = self.selected
            infos = stack.big_str(self.module)
            return (stack.display_name, infos)
        return None

    def _intern_inv_slot(self, stack):
        if stack is not None:
            emoji = self.get_emoji(stack.item.emoji)
            # max stack size is 99
            quant = f"{' ' if stack.quantity<=9 else ''}{stack.quantity}"
            return '{}``{}``'.format(emoji, quant)
        return '               '

    def _intern_equ_slot(self, stack):
        if stack is not None:
            emoji = self.get_emoji(stack.item.emoji)
            return '{}'.format(emoji)
        return '        '

    def equipment(self):  # FIXME: ajouter des emoji grisé qui reprenne chaque catégorie et les mettre dans les cases si aucuns items !
        equipment_size = len(self.get('equipment'))
        format_vars = {
            "hand_key": narr('inventory.equipment.hand_key'),
            "book_key": narr('inventory.equipment.book_key'),
            "armor_key": narr('inventory.equipment.armor_key'),
            "jewelry_key": narr('inventory.equipment.jewelry_key'),
            "tool_key": narr('inventory.equipment.tool_key'),
        }
        for idx in range(equipment_size):
            format_vars[f'_{idx}'] = self.equipment_slot(idx)
        return EQUIPMENT_TEMPLATE.format(**format_vars,)

    def inventory(self):
        """Generate the inventory space, return a tuple with name and desc"""
        out = ''
        inventory_size = len(self.get('inventory'))
        for idx in range(inventory_size):
            out += self.inventory_slot(idx)
            if (idx % INV_WIDTH) == (INV_WIDTH-1):
                out += '\n'
        return out

    # FIXME: tout mettre en noir et blanc et afficher si rien d'équiper (ou un emoji qui montre le 'vide')
    def equipment_slot(self, slot):
        """return the display of a slot base on the given stack"""
        stack = self.get('equipment')[slot]
        return f'[{self._intern_equ_slot(stack)}]'

    def inventory_slot(self, slot):
        stack = self.get('inventory')[slot]
        if slot == self.swap_slot:
            start = "↱ "
            end = " ↲"
        elif slot == self.cursor:
            start = "**▹**"
            end = "**◃**"
        else:
            start = "[  "
            end = "  ]"
        return '{}{}{}'.format(start, self._intern_inv_slot(stack), end)

    def set_sell_quantity(self,quantity):
        self.to_sell_stack = self.selected.copy()
        self.to_sell_stack.quantity = quantity


    def sell_0_embed(self):
        return discord.Embed(
            title=narr('inventory.sell_title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('inventory.sell_0_desc').format(item_name=self.selected.display_name)
        )

    def sell_1_embed(self):
        return discord.Embed(
            title=narr('inventory.sell_title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('inventory.sell_1_desc').format(
                stack_desc=self.to_sell_stack.short_str(self.module),
                value=self.to_sell_stack.sell_price,
                emoji=self.get_emoji('money'),
                )
        )

    def upgrade_embed(self):
        stack = self.selected
        equipment_desc = f"**{stack.display_name}**\n\n"

        bar = emoji_bar(8,stack.durability/stack.item.max_durability,'🟦','⬛',self.module)
        equipment_desc += f"{narr('durability')} : {bar} {stack.durability}/{stack.item.max_durability}"
        if self.repair_recap is not None:
            equipment_desc += f"**(+{self.repair_recap})**"
        equipment_desc += "\n\n"

        stat_list = []
        for stat,value in stack.stats_modifiers.get('add',{}).items():
            line = f"{narr(f'stats.{stat}')} : {value}"
            if (self.upgrade_recap is not None) and (stat in self.upgrade_recap['add']):
                line += f"**(+{self.upgrade_recap['add'][stat]})**"
            stat_list.append(line)
        
        for stat,value in stack.stats_modifiers.get('mult',{}).items():
            line = f"{narr(f'stats.{stat}')} : {value*100}%"
            if (self.upgrade_recap is not None) and (stat in self.upgrade_recap['mult']):
                line += f"**(+{self.upgrade_recap['mult'][stat]*100}%)**"
            stat_list.append(line)
        
        equipment_desc += "\n".join(stat_list)
        equipment_desc += "\n"

        return discord.Embed(
            title=narr('inventory.upgrade_title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('inventory.upgrade_desc').format(
                equipment_desc=equipment_desc,
                essence_desc=stack.upgrade_cost.short_str(self.module),
            )
        )

    def drop_embed(self):
        pass

    def give_embed(self):
        pass

    """
    Button methods
    """

    async def close(self):
        await self.disable()

    async def go_left(self):
        x = self.cursor
        w = INV_WIDTH
        self.cursor = ((x-1) % w)+((x//w)*w)
        await self.render()

    async def go_right(self):
        x = self.cursor
        w = INV_WIDTH
        self.cursor = ((x+1) % w)+((x//w)*w)
        await self.render()

    async def go_up(self):
        x = self.cursor
        w = INV_WIDTH
        t = len(self.get('inventory'))
        c = x-w
        if c < 0:
            c = (c % w)+w*((t//w)-1)
        self.cursor = c
        await self.render()

    async def go_down(self):
        x = self.cursor
        w = INV_WIDTH
        t = len(self.get('inventory'))
        c = x+w
        if c >= t:
            c = c % w
        self.cursor = c
        await self.render()

    async def swap(self):
        if self.swap_slot is not None:
            swap_slot = self.swap_slot
            self.swap_slot = None
            if swap_slot != self.cursor:
                # render is called here
                await self.module.api.swap_stacks(self.user, swap_slot, self.cursor)
        else:
            self.swap_slot = self.cursor
            await self.render()
        # don't render here because in first condition, api will rerender

    async def upgrade(self):
        if self.state == 'inv':
            if (self.selected is None) or (not self.selected.item.is_equipment):
                self.temp_notif = narr('inventory.notifications.cant_upgrade_this')
                return await self.render()
            
            self.state = 'upgrade'
            await self.remove_all_buttons()
            await self.render()
            await self.add_buttons('🔨','🔧','↩️')
        elif self.state == 'upgrade':
            try:
                self.upgrade_recap = await self.module.api.upgrade_equipment(self.user,self.cursor,1) # call render intern

                db_user = self.module.api.db_user(self.user)
                upgraded_stuff = db_user.inventory[self.cursor]
                await self.module.trigger_hook('upgrade_stuff', self.user, upgraded_stuff)
                self.upgrade_fail_streak = 0
            except MaxLevelException:
                self.temp_notif = narr('inventory.notifications.upgrade_maxed')
            except NotEnoughtResourcesException:
                self.temp_notif = narr('inventory.notifications.upgrade_no_resource')
            except UpgradeFailedException:
                self.upgrade_fail_streak += 1
                self.temp_notif = narr('inventory.notifications.upgrade_failed').format(fails=self.upgrade_fail_streak)
            await self.render()

    
    async def repair(self):
        try:
            await self.module.api.repair_equipment(self.user,self.cursor,1)
            self.repair_recap = 1

            # hook
            db_user = self.module.api.db_user(self.user)
            repaired_stuff = db_user.inventory[self.cursor]
            await self.module.trigger_hook('repair_stuff', self.user, repaired_stuff)
        except MaxDurabilityException:
            self.temp_notif = narr('inventory.notifications.repair_maxed')
        except NotEnoughtResourcesException:
            self.temp_notif = narr('inventory.notifications.repair_no_resource')
        await self.render()


    async def use_item(self):  # equipé et nul - équipé et outil - nul et outil
        if self.selected is not None:
            if self.selected.item.is_equipment:
                equ_slot = self.selected.item.equipment_slots
                if len(equ_slot) <= 1:
                    try:
                        db_user = self.module.api.db_user(self.user)
                        to_equip = db_user.inventory[self.cursor]
                        to_desequip = db_user.equipment[equ_slot[0]]
                        
                        await self.module.api.equip(self.user, self.cursor, equ_slot[0]) # can raise errors
                        
                        if to_equip is not None:
                            await self.module.trigger_hook('equip_stuff', self.user, to_equip)
                        if to_desequip is not None:
                            await self.module.trigger_hook('desequip_stuff', self.user, to_desequip) # only trigger in case of swap (kind of desequip)

                    except NoRequiredRankException:
                        self.temp_notif = narr('inventory.temp_notif.equip_no_rank')
                        await self.render()
                else:  # multiple choices
                    raise Exception('TODO : (equipe books and rings) ==> multi choice')
            elif self.selected.item.is_recipe:
                try:
                    await self.module.api.use_recipe(self.user, self.cursor)
                except InventoryFullException:
                    self.temp_notif = narr(
                        'inventory.temp_notif.inventory_full')
                    await self.render()
                except NotEnoughtResourcesException:
                    self.temp_notif = narr('inventory.temp_notif.no_resources')
                    await self.render()
            # conso etc ..
        else:
            # TODO: quand il y aura le stuff, ajouter un selecteur de quoi déséquiper, pour l'insant : osef
            equiped_tool = self.get('tool')
            if equiped_tool is not None:
                equ_slot = equiped_tool.item.equipment_slots
                if len(equ_slot) <= 1: # always true for tools
                    await self.module.api.desequip(self.user, self.cursor, equ_slot[0])
                    await self.module.trigger_hook('desequip_stuff', self.user, equiped_tool) # desequip 
                
    
    async def sell(self):
        if self.selected is None:
            return
        
        if self.selected.quantity == 1:
            self.set_sell_quantity(1)
            self.state = 'sell_1'
            await self.remove_all_buttons()
            await self.render()
            await self.add_buttons('🟩','🟥')
        else:
            self.state = 'sell_0'
            self.is_waiting_input = True
            await self.remove_all_buttons()
            await self.render()
            await self.add_buttons('↩️')

    async def accept(self):
        if self.state == 'sell_1':
            self.state = 'inv'
            quantity = self.to_sell_stack.quantity
            self.to_sell_stack = None

            to_sell = self.module.api.db_user(self.user).inventory[self.cursor]
            to_sell.quantity = quantity

            await self.remove_all_buttons()
            await self.module.api.sell_stack(self.user, self.cursor, quantity) # call render
            await self.add_buttons(*INV_BUTTONS)

            await self.module.trigger_hook('sell_stuff',self.user,to_sell)

    async def refuse(self):
        if self.state == 'sell_1':
            self.to_sell_stack = None
            self.state = 'inv'
            await self.remove_all_buttons()
            await self.render()
            await self.add_buttons(*INV_BUTTONS)

    async def go_back(self):
        # if (self.state == 'sell_0') or (self.state == 'upgrade):
        self.upgrade_recap = None
        self.repair_recap = None
        self.is_waiting_input = False
        self.state = 'inv'
        await self.remove_all_buttons()
        await self.render()
        await self.add_buttons(*INV_BUTTONS)