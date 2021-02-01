import asyncio
import discord
import random

from utility.loader import conf
from bases.module_base import Module
from objects.item import Stack
from objects.items.equipment import Tool
from modules.activity.panels.tool_panel import ToolPanel

ACTIVITY_DT = 10

class FishingModule(Module):
    # TODO: add efficiency to tools ==> effort
    """A chaque DT(constant) on ajoute la somme des effort (valeur de l'outil utilisé) des joueurs (clamper avec max_effort_per_round) à self.effort, quand self.effort atteint needed_effort, un joueur aléatoir (qui n'a pas de panel ouvert) des actif déclenche un événement de loot"""
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 10
    effort = 0

class MiningModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 20
    effort = 0

class PickingModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 30
    effort = 0

class AnimalHuntingModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 40
    effort = 0

class DiggingModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 50
    effort = 0

class InsectHuntingModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 60
    effort = 0

class ExplorationModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 70
    effort = 0

class NecromancyModule(Module):
    max_effort_per_round = 15
    needed_effort = 25
    activity_xp = 25
    effort = 0

class ActivityModule(Module):
    drop_balance = {} # {user:activity_loop_without_drop}
    # this dict will be used to balance the probability of event triger and allow everybody to drop

    async def main_loop(self):
        while True:
            await asyncio.sleep(ACTIVITY_DT)
            user_per_activity = {} # {'Fishing':[user1,user2], 'Mining':[user3]} ==> replace users with tuple of (user,tool)

            # create the dic of actives users
            vocs = self.main_bot.in_voc.copy()
            for user,voc_data in vocs.items():
                if voc_data['active']: # make active verify afk channel
                    db_user = self.api.db_user(user)
                    if db_user.tool is None:
                        continue
                    if not db_user.tool.is_usable:
                        continue
                    if db_user.energy <= 0:
                        continue
                    if db_user.active_infraction is not None:
                        continue

                    self.drop_balance[user] = self.drop_balance.get(user,0) + 1
                    module_name = db_user.tool.item.module_name
                    if module_name not in user_per_activity:
                        user_per_activity[module_name] = []
                    user_per_activity[module_name].append((user,db_user))

            activity_panels = []

            for mod in self.main_bot.modules:
                users = user_per_activity.get(mod.name,None)
                if users is not None:
                    round_effort = sum([db_user.tool.item.efficiency for u,db_user in users])
                    round_effort = min(round_effort,mod.max_effort_per_round)
                    mod.effort += round_effort
                    if mod.effort >= mod.needed_effort:
                        mod.effort = 0
                        already_active = self.activity_open_users(mod)
                        to_pick_from = [(user,db_user) for user,db_user in users if (user not in already_active)]
                        # up chance of successive non drop players
                        for user,db_user in to_pick_from[:]:
                            multiplica = self.drop_balance[user] - 1
                            for _ in range(multiplica):
                                to_pick_from.append((user,db_user))

                        if len(to_pick_from) > 0:
                            random_user,random_db_user = random.choice(to_pick_from)
                            p = self.use_tool(mod,random_user,random_db_user.tool)
                            # p = random_db_user.tool.item.use(mod,random_user)
                            activity_panels.append(p)

            for p in activity_panels:
                await p

    async def user_per_module(self,module):
        """Return all the users that are farming a specific activity (linked to a module)
        check for equiped tool, tool durability > 0, energy > 0 and user not in prison/isolation"""
        #TODO: si on deplace le code ici ca sera moins optimiser car on itérera in_voc pour chaque modules ..
        pass

    async def use_tool(self,mod,user,tool):
        channel = mod.get_channel(conf(f"activity.{mod.name}"))
        await tool.item.panel.create(channel,user,mod,tool)

    async def _on_ready(self):
        self.loop.create_task(self.main_loop())

    def activity_open_users(self,under_mod):
        """Return a list of user with a tool panel open"""
        users = []
        for panel in under_mod.panels[:]:
            if ToolPanel in panel.__class__.__bases__: # get only tool panels
                users.append(panel.user)
        return users