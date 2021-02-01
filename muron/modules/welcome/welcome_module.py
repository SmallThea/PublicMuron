import asyncio
import time

from utility.loader import narr, conf
from bases.module_base import Module
from utility.emoji import str_to_emoji
from modules.welcome.panels.welcome_panel import WelcomePanel

class WelcomeModule(Module):
    invites = []

    @property
    def welcome_channel(self):
        return self.get_channel(conf('welcome.channel'))

    async def _on_ready(self):
        self.invites = await self.guild.invites()
        print("Welcome run")

    async def _on_member_remove(self,member):
        # delete all panels
        for panel in self.all_panels:
            if panel.user == member:
                await panel.disable(delete=True)
        
        if self.api.already_exist(member):
            db_user = self.api.db_user(member)
            if db_user.is_ban:
                return
            return await self.main_bot.module_method('just_leave',member) # only call if the player exist !

    async def _on_member_join(self, member):
        """Get the inviter and if this is the first join then call the '_just_join' method as a module method (call on all modules)"""
        if member.bot:
            return
            
        last_invs = self.invites
        new_invs = await self.guild.invites()
        self.invites = new_invs
        
        first_join = not self.api.already_exist(member)

        no_match_inv = []
        for last in last_invs:
            match = False
            for new in new_invs:
                if last == new:
                    match = True
                    if last.uses != new.uses:
                        return await self.main_bot.module_method('just_join',member,last.inviter,first_join)
            if not match:
                no_match_inv.append(last)
            
        if len(no_match_inv) != 1: # can be 0 or more than 1 (in certain rare timing cases)
            inviter = None
        else:
            inviter = no_match_inv[0].inviter

        await self.main_bot.module_method('just_join',member,inviter, first_join) # call it like a module method

    async def _just_join(self,user,inviter,first_join):
        separator_roles = [self.guild.get_role(role_id) for role_id in conf('separator_roles')]
        await self.shared_add_user_roles(user,*separator_roles)
        if first_join:
            await WelcomePanel.create(self.welcome_channel, user, self,inviter)

    async def _just_leave(self,user):
        pass

    async def _on_invite_create(self, invite):
        self.invites.append(invite)

    async def _on_invite_delete(self, invite):
        if invite.uses != invite.max_uses:
            self.invites.remove(invite)

    async def _on_door_passed(self, user, inviter):
        await self.api.invited_by(user, inviter) # this will create the user if he respond correct
        role = self.guild.get_role(conf('rank.roles.0'))
        await self.shared_add_user_roles(user, role)
        channel = self.guild.get_channel(conf('join_leave_channel'))
        if inviter is None:
            await self.send(channel, narr('welcome.welcome_message_no_inviter').format(
                joiner_mention = user.mention,
            ))
        else:
            await self.send(channel, narr('welcome.welcome_message_inviter').format(
                joiner_mention = user.mention,
                inviter_name = inviter.display_name,
            ))
            inviter = self.guild.get_member(inviter.id) # cast to member | we keep the inviter a user before for having it as inviter even if he is not on the server
            await self.trigger_hook('invite', inviter, user)