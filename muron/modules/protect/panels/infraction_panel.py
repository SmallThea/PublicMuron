import discord
import asyncio

from bases.panel_base import Panel
from objects.rule import Rule, Infraction
from utility.loader import narr,conf

class InfractionPanel(Panel):
    disable_delay = 180
    delete_on_disable = True
    one_per_user = True

    mapping = {
        '🟨': {'callback': 'low', 'action': ''},
        '🟧': {'callback': 'medium', 'action': ''},
        '🟥': {'callback': 'hard', 'action': ''},
        '🟢': {'callback': 'accept', 'action': ''},
        '🔴': {'callback': 'cancel', 'action': ''},
    }
    base_buttons = ['🟨', '🟧','🟥']
    state = 'selection'  # validation # accept # cancel


    infraction = None

    guilty = None
    staff = None
    rule_id = None
    hardness = None
    recidive = None 
    

    @classmethod
    async def create(cls, channel, user, module, guilty, rule_id):
        panel = cls()
        panel.guilty = guilty # le coupable
        panel.rule_id = rule_id # la règle enfreint
        await panel.init(channel, user, module)
        return panel

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def selection_embed(self):
        return discord.Embed(
            title=narr('protect.infraction_panel.title').format(user=self.guilty.display_name,staff=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('protect.infraction_panel.selection_desc')
        )

    def validation_embed(self):
        kwargs = {
            'name':self.infraction.guilty.mention,
            'rule_index':self.infraction.rule.index,
            'hardness_word':narr(f'protect.infraction.hardness.{self.infraction.hardness}'),
            'hardness_emoji':('🟨', '🟧','🟥')[self.infraction.hardness-1],
            'rule_desc':self.infraction.rule.description,
            'sanction_info':self.infraction.sanction_info,
            'recidive_info':self.infraction.recidive_info,
        }
        return discord.Embed(
            title=narr('protect.infraction_panel.title').format(user=self.guilty.display_name,staff=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('protect.infraction_panel.validation_desc').format(**kwargs)
        )

    def accept_embed(self):
        return discord.Embed(
            title=narr('protect.infraction_panel.title').format(user=self.guilty.display_name,staff=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('protect.infraction_panel.accept_desc')
        )

    def cancel_embed(self):
        return discord.Embed(
            title=narr('protect.infraction_panel.title').format(user=self.guilty.display_name,staff=self.user.display_name),
            colour=discord.Colour.blurple(),
            description=narr('protect.infraction_panel.cancel_desc')
        )

    async def finalize_sanction(self):
        """Applique la sanction au joueur en question"""
        recap = await self.module.api.add_infraction(self.infraction)
        await self.module.apply_infraction(self.guilty,recap,context='clasic')
        
    """ Buttons """

    async def go_to_validation(self):
        db_user = self.module.api.db_user(self.guilty)
        self.recidive = db_user.infraction_recidive(self.rule_id)
        self.infraction = Infraction(self.guilty,self.user,self.rule_id,self.hardness,self.recidive)

        await self.remove_buttons('🟨', '🟧','🟥')
        await self.add_buttons('🟢', '🔴')
        self.state = 'validation'
        await self.render()

    async def low(self):
        self.hardness = 1
        await self.go_to_validation()

    async def medium(self):
        self.hardness = 2
        await self.go_to_validation()

    async def hard(self):
        self.hardness = 3
        await self.go_to_validation()

    async def accept(self):
        await self.finalize_sanction()
        self.state = 'accept'
        await self.disable(delete=True,delay=30)

    async def cancel(self):
        self.sate = 'cancel'
        await self.disable(delete=True,delay=30)