#TODO: détruire les welcome panel en cas de leave
#TODO: créer le user dans la db seulement dans le cas ou le joueur passe la porte

import discord
import asyncio

from bases.panel_base import Panel
from utility.loader import conf, narr


class WelcomePanel(Panel):
    disable_delay = 900  # 15 min
    reset_delay_on_interact = False
    delete_on_disable = True
    one_per_user = True

    mapping = {
        '0️⃣': {'callback': 'on_wrong', 'action': ''},
        '1️⃣': {'callback': 'on_wrong', 'action': ''},
        '2️⃣': {'callback': 'on_wrong', 'action': ''},
        '3️⃣': {'callback': 'on_correct', 'action': ''},
        '4️⃣': {'callback': 'on_wrong', 'action': ''},
        '5️⃣': {'callback': 'on_wrong', 'action': ''},
        '6️⃣': {'callback': 'on_wrong', 'action': ''},
        '7️⃣': {'callback': 'on_wrong', 'action': ''},
        '8️⃣': {'callback': 'on_wrong', 'action': ''},
        '9️⃣': {'callback': 'on_wrong', 'action': ''},
        '✔️': {'callback': 'on_accept', 'action': ''},
    }
    base_buttons = ['0️⃣', '1️⃣', '2️⃣', '3️⃣','4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

    state = 'question'  # wrong / # correct

    inviter = None
    answere_given = False

    @classmethod
    async def create(cls, channel, user, module, inviter):
        """Créer un panel dans le channel fournis en paramètre et authorise seulement l'utilisateur 
        passé en paramètre a intéragir avec, le module est nécéssaire pour le bon fonctionnement"""
        panel = cls()
        panel.inviter = inviter
        await panel.init(channel, user, module)
        return panel

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def question_embed(self):
        rules_channel = self.module.guild.get_channel(conf('rules_channel'))
        embed = discord.Embed(
            title=narr('welcome.panel.title'),
            colour=discord.Colour.blurple(),
            description=narr('welcome.panel.desc').format(rules=rules_channel.mention)  # if does not work use url instead
            )
        desc = ""
        for emoji, proposition in zip(self.base_buttons, narr('welcome.panel.responses')):
            desc += f"{emoji} : {proposition}\n"
        embed.add_field(name=narr('welcome.panel.responses_title'), value=desc, inline=False)
        return embed

    def wrong_embed(self):
        return discord.Embed(
            title=narr('welcome.panel.title'),
            colour=discord.Colour.blurple(),
            description=narr('welcome.panel.wrong_desc')
        )

    def correct_embed(self):
        return discord.Embed(
            title=narr('welcome.panel.title'),
            colour=discord.Colour.blurple(),
            description=narr('welcome.panel.correct_desc')
        )

    async def on_disable(self):
        if not self.answere_given:
            protect_module = self.module.module_by_name('protect')
            await protect_module.log_door_leave(self.user) # call when leave in front of the door

    async def auto_disable(self):
        await self.module.shared_kick_user(self.module.guild, self.user)

    """Buttons"""

    async def on_correct(self):
        self.state = 'correct'
        await self.remove_all_buttons()
        await self.add_buttons('✔️')
        await self.render()

    async def on_wrong(self):
        self.state = 'wrong'
        await self.remove_all_buttons()
        await self.add_buttons('✔️')
        await self.render()

    async def on_accept(self):
        self.answere_given = True
        protect_module = self.module.module_by_name('protect') # for logging 
        if self.state == 'wrong':
            await self.module.shared_kick_user(self.module.guild, self.user)
            # kick will triger the disable 
            await protect_module.log_door_fail(self.user)
        elif self.state == 'correct':
            await self.module.main_bot.module_method('on_door_passed',self.user, self.inviter)
            await self.disable(delete=True)
            await protect_module.log_door_sucess(self.user)
