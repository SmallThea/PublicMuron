import asyncio
import time
import discord
import re

# from objects.rule import InfractionRecap
from utility.loader import conf, narr
from bases.module_base import Module
from utility.emoji import str_to_emoji
from modules.protect.commands.clear_command import ClearCommand
from modules.protect.commands.infraction_command import InfractionCommand
from modules.protect.commands.release_command import ReleaseCommand
from modules.protect.commands.ban_command import BanCommand
from modules.protect.commands.unban_command import UnbanCommand
from modules.protect.commands.error_command import ErrorCommand
from modules.protect.commands.reset_command import ResetCommand, ResetallCommand

PRISON_ROLE = conf('protect.punished_roles.prison')
ISOLATION_ROLE = conf('protect.punished_roles.isolation')
PRISON_CHANNEL = conf('protect.prison_text_channel')
ISOLATION_CHANNEL = conf('protect.isolation_text_channel')
RELEASE_CHANNEl = conf('protect.release_text_channel')
LOG_CHANNEL = conf('protect.log_channel')

INVITE_REGEX = "(https?:\\/\\/)?(www\\.)?(discord\\.(gg|io|me|li)|discordapp\\.com\\/invite)\\/.+[a-z]"

class ProtectModule(Module):

    @property
    def rules_channel(self):
        return self.get_channel(conf('rules_channel'))
    @property
    def prison_role(self):
        return self.guild.get_role(PRISON_ROLE)

    @property
    def isolation_role(self):
        return self.guild.get_role(ISOLATION_ROLE)

    @property
    def prison_channel(self):
        return self.guild.get_channel(PRISON_CHANNEL)

    @property
    def isolation_channel(self):
        return self.guild.get_channel(ISOLATION_CHANNEL)

    @property
    def release_channel(self):
        return self.guild.get_channel(RELEASE_CHANNEl)

    @property
    def log_channel(self):
        return self.guild.get_channel(LOG_CHANNEL)

    def time_left_embed(self,user):
        db_user = self.api.db_user(user)
        infraction = db_user.active_infraction
        if infraction is None:
            return

        return discord.Embed(
            colour=discord.Colour.blurple(),
            description=narr('protect.time_left').format(name=user.mention,duration=infraction.time_left(to_str=True),rule_channel=self.rules_channel.mention)
        )

    async def _on_ready(self):
        await self.release_init()
        await self.set_perms()
        self.add_command(ClearCommand)
        self.add_command(InfractionCommand)
        self.add_command(ReleaseCommand)
        self.add_command(BanCommand)
        self.add_command(UnbanCommand)
        self.add_command(ErrorCommand)
        self.add_command(ResetCommand)
        self.add_command(ResetallCommand)
        print("Combat run")

    async def release_init(self):
        for user in (self.prison_role.members + self.isolation_role.members):
            db_user = self.api.db_user(user)
            infraction = db_user.active_infraction
            if infraction is not None:
                # await self.release_in(user,infraction.time_left()*60)
                await self.infraction_end(user,infraction)
            else: # should not happen but in case
                await self.release(user)

    async def set_perms(self):
        """Set the perm if not already done for every channel in the server"""
        for channel in self.guild.channels:
            await self.set_channel_perm(channel)

    async def set_channel_perm(self,channel):
        """Set the permission for text channel, do nothing if already done"""

        overwrites = channel.overwrites
        updated = False

        if self.prison_role not in overwrites:
            prison_perms = discord.PermissionOverwrite(speak=False,send_messages=False,add_reactions=False)
            overwrites[self.prison_role] = prison_perms
            updated = True

        if self.isolation_role not in overwrites:
            isolation_perms = discord.PermissionOverwrite(read_messages=False)
            overwrites[self.isolation_role] = isolation_perms
            updated = True

        if updated:
            await self.shared_edit_channel(channel, overwrites=overwrites)

    async def _on_guild_channel_create(self, channel):
        if channel.category_id == conf('voc.category_channel'): # voc handle this part itself
            return

        await self.set_channel_perm(channel)
        

    async def infraction_end(self,user,infraction):
        self.loop.create_task(self._infraction_end(user,infraction))

    async def _infraction_end(self,user,infraction):
        await asyncio.sleep(infraction.time_left()*60 + 1)
        db_user = self.api.db_user(user)
        if not db_user.is_ban:
            infraction_left = db_user.active_infraction
            if infraction_left is not None:
                await self.release(user,context='clasic')
                await self.log_infraction_end(user, infraction)

    async def release(self,user,context='clasic'):
        user = self.guild.get_member(user.id) # refresh
        if user is not None:
            to_remove = [role for role in (self.prison_role,self.isolation_role) if role in user.roles]
            await self.shared_remove_user_roles(user,*to_remove) #TODO: trouver les erreurs et try catch
            if context == 'clasic':
                await self.send(self.release_channel,narr('protect.release_text').format(name=user.mention))
            elif context == 'earlier':
                await self.send(self.release_channel,narr('protect.release_earlier_text').format(name=user.mention))

    async def apply_infraction(self,user,infraction,context='clasic'): # context ==> ['clasic','rejoin']
        if infraction.place == 'prison':
            await self.shared_add_user_roles(user,self.prison_role)
            if context == 'clasic':
                await self.send(self.prison_channel,narr('protect.to_prison_text').format(name=user.mention))
            elif context == 'rejoin':
                await self.send(self.prison_channel,narr('protect.back_with_infraction').format(name=user.mention))
        elif infraction.place == 'isolation':
            await self.shared_add_user_roles(user,self.isolation_role)
            # kick from voc if sent to isolation
            if user.voice is not None:
                if user.voice.channel is not None:
                    await self.module.shared_move_user(self.user, None)
            if context == 'clasic':
                await self.send(self.isolation_channel,narr('protect.to_isolation_text').format(name=user.mention))
            elif context == 'rejoin':
                await self.send(self.isolation_channel,narr('protect.back_with_infraction').format(name=user.mention))
        await self.infraction_end(user,infraction)

        if context=='clasic':
            await self.log_infraction_start(user, infraction)

    async def _just_join(self,user,inviter,first_join):
        if not first_join:
            db_user = self.api.db_user(user)

            if db_user.is_ban:
                return await self.shared_ban_user(self.guild,user)

            infraction = db_user.active_infraction
            if infraction is not None:
                await self.apply_infraction(user,infraction,context='rejoin')
        await self.log_join(user, inviter, first_join)


    async def _just_leave(self,user):
        # we use this insthead of on_member_remove because otherwise we need to check if the user exist in the db before doing actions 
        # we don't want to create the user here ! (self.api.db_user(user) do it)
        # don't trigger in case kicked by door !
        db_user = self.api.db_user(user)
        infraction = db_user.active_infraction
        if infraction is not None:
            if infraction.place == 'prison':
                await self.send(self.prison_channel,narr('protect.left_with_infraction').format(name=user.mention))
            elif infraction.place == 'isolation':
                await self.send(self.isolation_channel,narr('protect.left_with_infraction').format(name=user.mention))
        
        await self.log_leave(user)

    async def _on_message(self,message):
        if self.user in message.mentions:
            for role in message.author.roles:
                if (role == self.prison_role) or (role == self.isolation_role):
                    return await self.send(message.channel,embed=self.time_left_embed(message.author))

        await self.check_invites(message)

    async def check_invites(self,message):
        invite_reg = re.search(INVITE_REGEX, message.content)
        if invite_reg:
            allowed = [
                conf('staff_roles.administration_leader'),
                conf('staff_roles.administration'),
            ]
            for role in message.author.roles:
                if role.id in allowed:
                    return 
            invit_link = invite_reg.group(0).split(' ')[0]

            await self.shared_delete_message(message)
            await self.log_invite(message, invit_link)

    async def _on_message_delete(self, message):
        await self.log_message_delete(message)


    """ All log calls """

    async def send_log(self,content):
        await self.send(self.log_channel,embed=discord.Embed(
            color=discord.Color.blurple(),
            description=content,
        ))

    async def log_join(self, user, inviter, first_join):
        narr_end = 'join' if first_join else 're_join'
        await self.send_log(narr(f'protect.log.{narr_end}').format(
            name=user.mention,
            inviter_name=inviter.mention if (inviter is not None) else narr('unknown_user'),
        ))

    async def log_leave(self, user):
        await self.send_log(narr('protect.log.leave').format(
            name=user.mention,
        ))

    async def log_door_sucess(self, user):
        await self.send_log(narr('protect.log.door_sucess').format(
            name=user.mention,
        ))

    async def log_door_fail(self, user):
        await self.send_log(narr('protect.log.door_failed').format(
            name=user.mention,
        ))

    async def log_door_leave(self, user):
        await self.send_log(narr('protect.log.door_leave').format(
            name=user.mention,
        ))

    async def log_infraction_start(self, user, infraction): # infraction contain staff
        await self.send_log(narr('protect.log.infraction_start').format(
            recap_str=infraction.recap_str(user.id),
        ))

    async def log_infraction_end(self, user, infraction):
        await self.send_log(narr('protect.log.infraction_end').format(
            name=user.mention,
        ))
    
    async def log_infraction_release(self, user, infraction):
        await self.send_log(narr('protect.log.infraction_release').format(
            name=user.mention,
            releaser=f'<@!{infraction.releaser_id}>',
        ))

    async def log_ban(self, user_id, staff):
        await self.send_log(narr('protect.log.ban').format(
            name=f'<@!{user_id}>',
            staff_name=staff.mention,
        ))
    
    async def log_unban(self, user_id, staff):
        await self.send_log(narr('protect.log.unban').format(
            name=f'<@!{user_id}>',
            staff_name=staff.mention,
        ))

    async def log_invite(self,message, invite_link): # message is the instance not the str
        await self.send_log(narr('protect.log.invite').format(
            name=message.author.mention,
            invitation=invite_link,
            channel=message.channel.mention,
            content=message.content[:250],
        ))
    
    async def log_message_delete(self, message): # message is the instance not the str
        await self.send_log(narr('protect.log.message_delete').format(
            name=message.author.mention,
            content=message.content[:250],
            channel=message.channel.mention,
        ))