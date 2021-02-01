import discord
import math

from bases.panel_base import Panel
from utility.loader import narr
from api.models.user import InventoryFullException, NotEnoughtResourcesException

ITEM_PER_PAGE = 15

#TODO: ajouter dans basic la boucle qui fait payer les taxes de banques à tout le monde
#TODO: étudier le cas d'ajouter un role a des gens, les pings puis enlever le role 

class BankPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = True
    delete_on_disable = False
    one_per_user_global = True

    tracked_keys = ['bank','bank_tax']
    mapping = {
        '◀️': {'callback': 'go_left', 'desc': ""},
        '🟥': {'callback': 'close', 'desc': ""},
        '▶️': {'callback': 'go_right', 'desc': ""},
        '✔️': {'callback': 'accept', 'desc':""},
        '❌': {'callback': 'refuse', 'desc':""},
    }
    base_buttons = ['◀️', '🟥', '▶️',]

    is_waiting_input = True
    page_index = 0
    selected_index = None

    state = 'pages' # pages / retrieve

    cumulative_errors = 0
    max_cumulative_errors = 3 # when reached automaticaly quit the panel

    @property
    def total_pages(self):
        return math.ceil(len(self.get('bank')) / ITEM_PER_PAGE)

    async def user_updated(self, keys):
        if self.page_index >= self.total_pages:
            self.page_index = max(0,self.page_index-1)
        await self.render()

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def pages_embed(self):
        embed = discord.Embed(
            title=narr('bank.title').format(name=self.user.display_name) + f" ┃ {self.page_index+1}/{max(1,self.total_pages)}",
            colour=discord.Colour.blurple(),
        )
        desc = ""
        to_itterate = [e for e in enumerate(self.get('bank'))]
        for index, stack in to_itterate[self.page_index*ITEM_PER_PAGE:(self.page_index+1)*ITEM_PER_PAGE]:
            desc += f"``{str(index).ljust(3, ' ')}`` : {stack.to_str(self.module)}\n"
        if len(to_itterate) == 0:
            desc += f"{narr('bank.nothing')}\n"

        # desc += f"\n{narr('bank.tax')} : **{self.get('bank_tax')}** {self.get_emoji('money')}"
        desc += "\n"
        desc += narr('bank.tax_text').format(value=self.get('bank_tax'),emoji=self.get_emoji('money'))
        desc += f"\n\n{narr('bank.instruction')}"

        embed.description = desc
        return embed

    def retrieve_embed(self):
        embed = discord.Embed(
            title=narr('bank.title').format(name=self.user.display_name),
            colour=discord.Colour.blurple(),
        )
        stack = self.get('bank')[self.selected_index]
        # desc = "**======================================**\n"
        desc = f"**{stack.display_name}**\n"
        desc += f"{stack.big_str(self.module)}\n"
        desc += "**\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_**\n\n"
        desc += f"{narr('bank.retrieve_desc')}"
        embed.description = desc
        return embed

    """
    Button methods
    """

    async def go_left(self):
        if self.total_pages > 0:
            self.page_index = self.page_index - 1 if (self.page_index > 0) else self.total_pages - 1
            await self.render()

    async def go_right(self):
        if self.total_pages > 0:
            self.page_index = (self.page_index + 1)%self.total_pages
            await self.render()

    async def accept(self):
        self.state = 'pages'
        self.is_waiting_input = True
        await self.remove_buttons('✔️', '❌')
        await self.add_buttons('◀️', '🟥', '▶️')
        try:
            self.temp_notif = narr('bank.notifications.retrieved')
            await self.module.api.remove_bank_stack(self.user,self.selected_index) # this will update the bank (so place notif before ^)
        except InventoryFullException:
                self.temp_notif = narr('bank.notifications.inventory_full')
                await self.render()

    async def refuse(self):
        self.is_waiting_input = True
        self.state = 'pages'
        await self.remove_buttons('✔️', '❌')
        await self.add_buttons('◀️', '🟥', '▶️')
        await self.render()

    async def close(self):
        await self.disable()

    async def input_handling(self, msg):
        try:
            index = int(msg)
            if (index < 0) or (index >= len(self.get('bank'))):
                raise Exception()
            self.selected_index = index
        except:
            self.is_waiting_input = True

            self.cumulative_errors += 1
            if self.cumulative_errors >= 3:
                await self.disable()
            else:
                self.temp_notif = narr('bank.notifications.wrong_input')
                await self.render()
        else:
            await self.remove_buttons('◀️', '🟥', '▶️')
            await self.add_buttons('✔️', '❌')
            self.state = 'retrieve'
            await self.render()
