import asyncio
import discord

from utility.loader import conf, narr
from bases.module_base import Module
from objects.item import Stack, Item
from modules.quest.commands.quest_command import QuestCommand


class QuestModule(Module):
    hooks = {} # {user: [hook_name, hook_name, ]}

    async def _on_ready(self):
        print("Quest run")
        self.add_command(QuestCommand)
        self.init_hook_list()

    async def _on_member_remove(self,member):
        if member in self.hooks:
            del self.hooks[member]

    async def _just_join(self,user,inviter,first_join):
        if not first_join:
            self.update_user_hooks(user)
            await self.give_roles_rewards(user)

    async def _on_door_passed(self, user, inviter):
        self.update_user_hooks(user)

    def update_user_hooks(self, user):
        db_user = self.api.db_user(user)   
        quest_hooks = db_user.active_hooks # list of hook_name
        if quest_hooks is not None:
            self.hooks[user] = quest_hooks

    async def give_roles_rewards(self, user):
        db_user = self.api.db_user(user)
        roles_to_add = []
        for user_quest in db_user.quests:
            chapters = user_quest.quest.chapters
            finished_chapters = len(chapters) if (user_quest.finished) else user_quest.chapter_index
            
            for chapter,_ in zip(chapters,range(finished_chapters)):
                role_reward = chapter.role_rewards
                if role_reward is not None:
                    roles_to_add.append(role_reward)
        
        if len(roles_to_add) > 0:
            roles = [self.guild.get_role(role_id) for role_id in roles_to_add]
            await self.shared_add_user_roles(user, *roles)

    def init_hook_list(self):
        for user in self.guild.members: # tout les membres du serveur
            if len(user.roles) > 0 and not user.bot: # pass the door and not bots
                self.update_user_hooks(user)

    async def handle_hook(self, hook_name, user, *args, **kwargs):
        if user not in self.hooks:
            return [] # i don't thing it's needed but in case 
        
        modified_vars = []
        if kwargs.get('inside_api',False):
            del kwargs['inside_api']
            returned_tuple, modified_vars = await self.api._handle_quest_hook(hook_name, user, *args, **kwargs)
            finished_chapters, can_be_finished_chapters, self.hooks[user] = returned_tuple
        else:
            finished_chapters, can_be_finished_chapters, self.hooks[user] = await self.api.handle_quest_hook(hook_name, user, *args, **kwargs)

        for chapter in finished_chapters:
            # Handle success, give role and send notification
            if chapter.role_rewards is None:
                continue
            roles = [self.guild.get_role(role_id) for role_id in chapter.role_rewards]
            await self.shared_add_user_roles(user, *roles)
            sucess_name = narr(f'success.list.{chapter.quest_name}.name')
            sucess_desc = narr(f'success.list.{chapter.quest_name}.desc')
            role = self.guild.get_role(chapter.role_rewards[0])
            message = narr('success.notification').format(
                success_name=sucess_name,
                success_emoji=role.mention,
                success_desc=sucess_desc,
            )
            await self.send_notification(user, message, color=role.color)
        for chapter in can_be_finished_chapters:
            # Handle normal quest, send notification for finishing
            message = narr(f'quest.end_notification').format(chapter_name=chapter.display_name,)
            await self.send_notification(user, message, color=discord.Color.purple())
        return modified_vars