import discord
import functools
import uuid
import asyncio
import random
from utility.other import merge

from api.models.user import (
    User, 
    InventoryFullException, 
    NotEnoughtResourcesException,
    NotEnoughtEnergyException,
    NotEnoughtMoneyException,
    MaxLevelException,
    MaxDurabilityException,
    UpgradeFailedException,
    AllreadyBanException,
    NotAllreadyBanException,
    NoRequiredRankException,
    QuestNotFoundException,
    ChapterOutOfRangeException,
    WEAPON_SLOT,
    SHIELD_SLOT,
    SPELL1_SLOT,
    SPELL2_SLOT,
    SPELL3_SLOT,
    HELMET_SLOT,
    CHESTPLATE_SLOT,
    GLOVES_SLOT,
    BOOTS_SLOT,
    RING1_SLOT,
    RING2_SLOT,
    NECKLESS_SLOT,
    TOOL_SLOT,
    )
from objects.rank import Rank, RANK_LIST
from objects.item import Item, Stack
from utility.loader import narr, conf

#TODO: async driver | mongoengine

def queue_method(func):
    """Make a database method work with a global queue system for synchronisation between async funcs"""
    @functools.wraps(func)
    async def inner(self, *args, **kwargs):
        queue_id = str(uuid.uuid1())
        self.queue.append(queue_id)
        # print(func,self.queue)
        while self.queue[:][0] != queue_id:
            await asyncio.sleep(0.001)

        try:
            output = await func(self, *args, **kwargs)
        except Exception as e:
            del self.queue[0]
            raise e
        else:    
            del self.queue[0]
            return output
    return inner

def cache_user_method(func):
    """Make a database method cache a user, the metehod NEED TO HAVE user IN PARAM"""
    @functools.wraps(func)
    async def inner(self, user, *args, **kwargs):
        if isinstance(user, discord.abc.User):
            self._cache_user_before_changes(user.id)
        elif isinstance(user, int):
            self._cache_user_before_changes(user)
        elif isinstance(user, User):
            self._cache_user_before_changes(user.user_id)
        return await func(self, user, *args, **kwargs)
    return inner
        
def modified_from_cache(old_user, new_user, keys):
    """Given two db_users and a list of keys, return the modified {key: increment_var} dict"""
    modified_dict = {}
    for key in keys:
        old = getattr(old_user,key)
        new = getattr(new_user,key)
        if isinstance(old,int):
            new = new - old
        modified_dict[key] = new
    return modified_dict



class Api:
    """Class a instancier une fois dans le bot principale et le rendre accessible depuis les modules, il servira d'intémédiaire avec la db"""

    queue = None
    hooks = None
    cached_users = None


    """""""""""""""""""""""""""""""""""

            INTERN METHODS 

    """""""""""""""""""""""""""""""""""


    def __init__(self, main_bot):
        self.main_bot = main_bot
        self.queue = []
        self.hooks = {} # {user: [hook_name, hook_name]} # link user with needed hooksh
        self.cached_users = {} # {user_id: db_user} # store old db_users before modification for extracting the modified values


    def _cache_user_before_changes(self, user_id): # for the moment this will only work with Integer values and not list like 'inventory'
        """Store a version before modification of a user, for extracting field that have been updated by comparing
        This cache created will be used and removed inside _hook_keys"""
        if user_id not in self.cached_users:
            db_user = self.db_user(user_id)
            self.cached_users[user_id] = db_user

    #TODO: handle hooks
    async def _user_change(self, db_user, *keys):
        """Update panels when a user change"""
    
        modified = await self._hook_keys(db_user, *keys)
        if len(modified) > 0:
            db_user = self.db_user(db_user.user_id) # get a new user with updated values
            keys = merge(list(keys), modified)
    
        for module in self.main_bot.modules:
            for panel in module.panels[:]:
                if panel.tracked_keys is not None:
                    if (panel.user.id == db_user.user_id):
                        updated = False
                        for key in keys:
                            if key in panel.tracked_keys:
                                panel.user_values[key] = getattr(db_user, key)
                                updated = True
                        if updated:
                            await panel.user_updated(keys)
                        
                        if 'rank' in keys:
                            await self.update_rank_role(db_user)

        # be sure to always keep the quests hooks updated
        if 'quest' in keys:
            quest_module = self.main_bot.module_by_name('quest')
            user = quest_module.guild.get_member(db_user.user_id)
            if user is not None:
                quest_hooks = db_user.active_hooks
                if quest_hooks is not None:
                    self.hooks[user] = quest_hooks



    async def _hook_keys(self, db_user, *keys):
        """Trigger quests based on modification of user keys (money, xp, etc)"""
        modified_vars = []
        mod = self.main_bot.available_mod_bot
        user = mod.guild.get_member(db_user.user_id)
        
        if user is None:
            return modified_vars

        try:
            old_user = self.cached_users.pop(db_user.user_id)
        except:
            raise Exception("Try to get a user that have not beed cached before !")

        modified_dict = modified_from_cache(old_user, db_user, keys)
        
        for key, value in modified_dict.items():
            if key != 'quests':
                modified = await mod.trigger_hook(key, user, value, inside_api=True) #FIXME: appeller avec la valeur d'incrément et pas la nouvelle value 
                #TODO: solution ? :décorateur sur toute les méthodes d'api qui cache les valeurs au début, et appelle _user_change à la fin
                merge(modified_vars, modified)

        if len([var for var in modified_vars if (var != 'quests')]) > 0: # modified more than quest
            modified = await self._hook_keys(db_user,*modified_vars) # recursive
            merge(modified_vars,modified)
        
        return modified_vars

    async def update_rank_role(self,db_user):
        user = self.main_bot.guild.get_member(db_user.user_id)
        # user_rank = db_user.rank
        user_roles = [role.id for role in user.roles]
        to_remove = []
        to_add = self.main_bot.guild.get_role(db_user.rank.role_id)
        for rank in Rank.ranks():
            if (rank.role_id in user_roles) and (rank.role_id != to_add.id):
                to_remove.append(self.main_bot.guild.get_role(rank.role_id))
        await self.main_bot.shared_add_user_roles(user,to_add)
        await self.main_bot.shared_remove_user_roles(user,*to_remove)


    async def handle_level_up(self, user_id, levels):
        """Handle level up message (call the level up module here)"""
        narrs = narr('level_up')
        welcome_bots = [mod for mod in self.main_bot.modules if mod.name in narrs.keys()]
        for level in levels:
            mod = random.choice(welcome_bots)
            user = mod.guild.get_member(user_id)
            messsage = narr(f'level_up.{mod.name}', rand=True).format(name=user.mention, level=level)
            await mod.send_notification(user, messsage)

            level_role_id = conf('level_ranks').get(str(level),None)
            if level_role_id is not None:
                role_mod = self.main_bot.available_mod_bot
                await role_mod.shared_add_user_roles(user,role_mod.guild.get_role(level_role_id))


    def all_db_user(self):
        return [db_user for db_user in User.objects()]

    def db_user(self, user_obj):
        """Used internaly for accessing the db_user, can also be used outside for visualisation purpouse (never save user out of this API)"""
        if isinstance(user_obj, discord.abc.User):
            return User.by_id(user_obj.id, create_if_none=True)
        elif isinstance(user_obj, int):
            return User.by_id(user_obj, create_if_none=True)
        elif isinstance(user_obj, User):
            return user_obj

    def already_exist(self,user):
        if isinstance(user, discord.abc.User):
            return User.by_id(user.id, create_if_none=False) is not None
        raise Exception('Wrong type passed (need discord user)')


    """""""""""""""""""""""""""""""""""

            DEBUGING METHODS

    """""""""""""""""""""""""""""""""""
    
    @queue_method
    async def delete_user(self, user):
        db_user = self.db_user(user)
        db_user.delete()
    
    @queue_method
    async def delete_all_users(self):
        for db_user in self.all_db_user():
            db_user.delete()


    """""""""""""""""""""""""""""""""""

              GLOBAL METHODS

    """""""""""""""""""""""""""""""""""

    @queue_method
    async def update_rank_prices(self):
        ranks = {}
        skip_first = True
        for rank_cls in RANK_LIST:
            if skip_first:
                skip_first = False
                continue
            ranks[rank_cls] = 0
        for db_user in User.objects():
            if db_user._rank > 0:
                ranks[db_user.rank.__class__] += 1

        total = sum([members for members in ranks.values()])
        if total != 0:
            for rank_cls, members in ranks.items():
                rank_cls.real_proportion = members/total

    @queue_method
    async def energy_loop(self): # FIXME: need to be optimized
        updated = []
        for db_user in User.objects():
            if db_user.energy < db_user.energy_max:
                self._cache_user_before_changes(db_user.user_id)
                db_user.energy += 1
                db_user.save()
                updated.append(db_user)
        for db_user in updated:
            await self._user_change(db_user, 'energy')

    async def bank_tax_loop(self): # FIXME: need to be optimized
        updated = []
        for db_user in User.objects():
            bank_tax = db_user.bank_tax
            money = db_user.money
            if (bank_tax > 0) and (money > 0):
                self._cache_user_before_changes(db_user.user_id)
                db_user.money = max(0,money-bank_tax)
                db_user.save()
                updated.append(db_user)
        for db_user in updated:
            await self._user_change(db_user, 'money')


    @queue_method
    async def voc_actives(self, dt, xp, users_vocs):
        for user, vocal_time in users_vocs.items():
            db_user = self.db_user(user)
            self._cache_user_before_changes(db_user.user_id)
            db_user.vocal_time += vocal_time
            modified, _ = await self._add_xp(db_user, xp)
            modified.append('vocal_time')
            await self._user_change(db_user, *modified)

    @queue_method
    async def message_actives(self, dt, xp, users_messages):
        for user, message_sent in users_messages.items():
            db_user = self.db_user(user)
            self._cache_user_before_changes(db_user.user_id)
            db_user.message_sent += len(message_sent)
            modified, _ = await self._add_xp(db_user, xp)
            modified.append('message_sent')
            await self._user_change(db_user, *modified)

    @queue_method
    async def tax_loop(self):  # FIXME: need to be optimized
        """Make all the players pay there taxe and unrank them if needed"""
        updated = {}
        for db_user in User.objects():
            if db_user._rank > 0:
                self._cache_user_before_changes(db_user.user_id)
                unrank = db_user.pay_tax()
                db_user.save()
                keys = []
                if unrank:
                    keys.append('rank')
                if db_user._rank > 0:
                    keys.append('money')
                updated[db_user] = keys
        for db_user, keys in updated.items():
            await self._user_change(db_user, *keys)


    """""""""""""""""""""""""""""""""""

                   RANK

    """""""""""""""""""""""""""""""""""

    @queue_method
    @cache_user_method
    async def rank_up(self, user):
        db_user = self.db_user(user)
        next_rank = db_user.rank.next_rank
        if (next_rank is not None) and (db_user.money >= next_rank.price) and (db_user.level >= next_rank.needed_level):
            db_user._rank += 1
            db_user.money -= next_rank.price
            db_user.save()
            await self._user_change(db_user, 'money', 'rank')
        else:
            raise Exception('Try to rank up without all condition filled')
    
    @queue_method
    @cache_user_method
    async def rank_down(self, user):
        db_user = self.db_user(user)
        pre_rank = db_user.rank.pre_rank
        if (pre_rank is not None):
            modified_var = ['rank',]

            db_user._rank -= 1

            equiped_tool = db_user.tool
            if (equiped_tool is not None) and (equiped_tool.item not in db_user.rank.allowed_tools):
                db_user.desequip(TOOL_SLOT,None)
                modified_var += ('tool','equipment','inventory','bank')
            db_user.save()
            await self._user_change(db_user, *modified_var)
        else:
            raise Exception('Try to rankdown without all condition filled')


    """""""""""""""""""""""""""""""""""

                   QUESTS 

    """""""""""""""""""""""""""""""""""


    async def _handle_quest_hook(self, hook_name, user, *args, **kwargs):
        module = self.main_bot.available_mod_bot
        db_user = self.db_user(user)
        self._cache_user_before_changes(db_user.user_id)
        quests = db_user.quests
        impact = False # for checker, hook can be triggered but don't do anything on triggers
        finished_chapters = []
        finishable_chapters = []
        modified_vars = []
        for quest in quests:
            if quest.finished:
                continue
            if hook_name in quest.active_hooks: # here, quest are UserQuest
                influence, finished_chapter, finishable_chapter = quest.trigger_hook(hook_name, user, module, *args, **kwargs) 
                
                #FIXME: make the to methodes return list, because a simple hook can finish multiple quests (if only ToReach + auto_finish)

                if influence:
                    impact = True
                if finished_chapter is not None:
                    finished_chapters.append(finished_chapter)
                    if finished_chapter.rewards is not None:
                        modified = await self._add_stuffs(db_user, finished_chapter.rewards)
                        for var in modified: #TODO: add values to a list without 'doublons'
                            if var not in modified_vars:
                                modified_vars.append(var)
                if finishable_chapter is not None:
                    finishable_chapters.append(finishable_chapter)
        if impact:
            db_user._quests = [quest.to_dict() for quest in quests]
            db_user.save()
            modified_vars += ('quests',)

        returned_tuple = (finished_chapters, finishable_chapters, db_user.active_hooks)
        return returned_tuple, modified_vars


    @queue_method
    async def handle_quest_hook(self, hook_name, user, *args, **kwargs):
        """Handle a hook, modify quest, and return finished and finishable chapters + the new hook list"""
        returned_tuple, modified_vars = await self._handle_quest_hook(hook_name, user, *args, **kwargs)
        db_user = self.db_user(user)
        await self._user_change(db_user, *modified_vars)
        return returned_tuple


    @queue_method
    @cache_user_method
    async def add_quest(self, user, quest_name):
        """Exceptionnaly we need module here for initialising the quest goals"""
        db_user = self.db_user(user)
        db_user.add_quest(quest_name, user, self.main_bot.available_mod_bot)
        db_user.save()
        await self._user_change(db_user, 'quests')

    @queue_method
    @cache_user_method
    async def remove_quest(self, user, quest_name):
        db_user = self.db_user(user)
        db_user.remove_quest(quest_name)
        db_user.save()
        await self._user_change(db_user, 'quests')

    @queue_method
    @cache_user_method
    async def finish_quest_chapter(self, user, quest_name):
        modified_var = ['quests',]
        db_user = self.db_user(user)
        finished_chapter = db_user.finish_quest_chapter(quest_name, user, self.main_bot.available_mod_bot)

        if finished_chapter.rewards is not None:
            modified_var += await self._add_stuffs(db_user, finished_chapter.rewards)

        db_user.save()
        await self._user_change(db_user, *modified_var)
        return finished_chapter

    @queue_method
    @cache_user_method
    async def set_quest_chapter(self, user, quest_name, chapter_index):
        db_user = self.db_user(user)
        # can raise QuestNotFoundException or ChapterOutOfRangeException
        db_user.set_quest_chapter(quest_name, chapter_index, user, self.main_bot.available_mod_bot)
        db_user.save()
        await self._user_change(db_user, 'quests')


    """""""""""""""""""""""""""""""""""

                   STACKS

    """""""""""""""""""""""""""""""""""

    @queue_method
    async def add_stuffs(self, user, stuffs):
        db_user = self.db_user(user)
        modified_var = self._add_stuffs(db_user, stuffs) # cached here
        db_user.save()
        await self._user_change(db_user, *modified_var)


    async def _add_stuffs(self,db_user, stuffs):
        """Add a lot of stuffs to the player, used by quest for quest rewards
        stuffs is a dict of things to add : C[money, gems, xp, stacks]
        a db_user should be passed in param, the user is not save at the end of the process
        """
        if not isinstance(db_user, User):
            raise Exception('A db_user should be passed in param not anything else')

        self._cache_user_before_changes(db_user.user_id)

        modified = []
        for key, value in stuffs.items():
            if key == 'stacks':
                db_user.add_stacks(*value)
                modified.append('inventory')
                modified.append('bank') #FIXME: not always
            elif key == 'xp':
                modified += (await self._add_xp(db_user, value))[0] #FIXME: this may cause some issues (made for being called last '__')
            else:
                setattr(db_user, key, getattr(db_user, key) + value)
                modified.append(key)
        return modified


    @queue_method
    @cache_user_method
    async def remove_bank_stack(self,user, index):
        """Remove a stack from the bank and add it to the inventory, can raise InventoryFullException if player don't have place for retrieving"""
        db_user = self.db_user(user)
        stack = db_user.get_bank_stack(index)
        if db_user.have_place_for(stack):
            db_user.remove_bank_stack(index)
            db_user.add_stacks(stack)
            db_user.save()
            await self._user_change(db_user, 'inventory','bank','bank_tax')
        else:
            raise InventoryFullException()

    @queue_method
    @cache_user_method
    async def claim_loot(self,user):
        db_user = self.db_user(user)
        try:
            stack_loot = db_user.claim_loot()
        except Exception as e:
            raise e
        else:
            db_user.save()
            await self._user_change(db_user, 'inventory','energy','bank','bank_tax') #FIXME: find a clean way to check if the bank has been modified
            return stack_loot


    @queue_method
    @cache_user_method
    async def add_stacks(self, user, *stacks):
        """Add a stacks to user inventory"""
        db_user = self.db_user(user)
        db_user.add_stacks(*stacks)
        db_user.save()
        await self._user_change(db_user, 'inventory')

    """""""""""""""""""""""""""""""""""

                MODERATION

    """""""""""""""""""""""""""""""""""
        

    @queue_method
    async def ban(self, user):
        db_user = self.db_user(user)
        if db_user.is_ban:
            raise AllreadyBanException()
        db_user.is_ban = True
        db_user.save()

    @queue_method
    async def unban(self, user):
        db_user = self.db_user(user)
        if not db_user.is_ban:
            raise NotAllreadyBanException()
        db_user.is_ban = False
        db_user.save()


    @queue_method
    async def add_infraction(self,infraction):
        """Add a infraction about a user, return a InfractionRecap instance"""
        db_user = self.db_user(infraction.guilty)
        recap = db_user.add_infraction(infraction) # applique la date de libération
        db_user.save()
        await self._user_change(db_user, 'infractions')
        return recap

    @queue_method
    async def release_user(self,user, staff):
        db_user = self.db_user(user)
        infraction_recap = db_user.release(staff.id)
        db_user.save()
        await self._user_change(db_user, 'infractions')
        return infraction_recap


    """""""""""""""""""""""""""""""""""

                OTHER 

    """""""""""""""""""""""""""""""""""

    @queue_method
    @cache_user_method
    async def upgrade_equipment(self, user, index, quantity):   
        db_user = self.db_user(user)
        try:
            upgrade_recap = db_user.upgrade_equipment(index, quantity) # can raise exception (catch in the inventory)
        except UpgradeFailedException:
            db_user.save()
            await self._user_change(db_user, 'inventory')
            raise UpgradeFailedException()
        else:
            db_user.save()
            await self._user_change(db_user, 'inventory')
            return upgrade_recap

    @queue_method
    @cache_user_method
    async def repair_equipment(self,user, index, quantity):
        db_user = self.db_user(user)
        db_user.repair_equipment(index, quantity) # can raise exception (catch in the inventory)
        db_user.save()
        await self._user_change(db_user, 'inventory')

    @queue_method
    @cache_user_method
    async def buy_base_tool(self,user):
        db_user = self.db_user(user)
        tool = db_user.rank.gain_tools[0]
        sub = db_user.money - int(tool.buy_price / 3)
        if sub >= 0:
            tool_stack = Stack(tool.name,1)
            db_user.money = sub
            db_user.add_stacks(tool_stack)
            db_user.save()
            await self._user_change(db_user, 'money','inventory','bank','bank_tax')
            return tool_stack
        else:
            raise NotEnoughtMoneyException(-sub)
    

    @queue_method
    @cache_user_method
    async def add_energy(self, user, value):
        db_user = self.db_user(user)
        if db_user.energy < db_user.energy_max:
            db_user.energy += min(db_user.energy+value, db_user.energy_max)
            db_user.save()
            await self._user_change(db_user, 'energy')


    @queue_method
    @cache_user_method
    async def add_money(self, user, quant):
        db_user = self.db_user(user)
        db_user.money += quant  # can be negative
        if db_user.money < 0:
            raise Exception(
                'Try to set the money of a user to a negative value')
        db_user.save()
        await self._user_change(db_user, 'money')
        return db_user.money

    @queue_method
    @cache_user_method
    async def equip(self, user, inv_idx, equ_idx):
        db_user = self.db_user(user)
        db_user.equip(inv_idx, equ_idx) # can raise errors
        db_user.save()
        modified_var = ['inventory','equipment',]
        if equ_idx == TOOL_SLOT:
            modified_var.append('tool')
        #TODO: adapt to other stuff
        await self._user_change(db_user, *modified_var)
    

    @queue_method
    @cache_user_method
    async def desequip(self, user,  inv_idx, equ_idx):
        db_user = self.db_user(user)
        db_user.desequip(equ_idx, inv_idx)
        db_user.save()
        modified_var = ['inventory','equipment',]
        if equ_idx == TOOL_SLOT:
            modified_var.append('tool')
        #TODO: adapt to other stuff
        await self._user_change(db_user, *modified_var)

    @queue_method
    @cache_user_method
    async def use_recipe(self, user, inv_idx):
        db_user = self.db_user(user)
        # can raise exception (catch in the inventory)
        db_user.use_recipe(inv_idx)
        db_user.save()
        await self._user_change(db_user, 'inventory')

    @queue_method
    @cache_user_method
    async def buy_market(self, user, market, coords):
        """Buy a item from a market, give the money to market owner and the item to the buyer"""
        pass

    @queue_method
    @cache_user_method
    async def sell_stack(self,user,index,quantity):
        db_user = self.db_user(user)
        db_user.sell_stack(index,quantity)
        db_user.save()
        await self._user_change(db_user, 'inventory', 'money')
    
    @queue_method
    async def invited_by(self, joiner, inviter):
        """Create the joiner for the first time and assigna  inviter if not None"""
        joiner = self.db_user(joiner) # saved here if non existent
        if inviter is not None:
            inviter = self.db_user(inviter)
            if joiner.inviter is None:
                joiner.inviter = inviter
                joiner.save()

    @queue_method
    @cache_user_method
    async def tool_damage(self, user):
        """Remove one durability from the equiped tool and break it if the durabiliy reach 0, return the current equiped tool (None if broken)"""
        db_user = self.db_user(user)
        db_user.tool_damage()
        db_user.save()
        await self._user_change(db_user, 'equiped_tool')
        return db_user.equiped_tool

    @queue_method
    @cache_user_method
    async def swap_tool(self, user, inv_idx):
        """Switch the tool slot of the user with a other tool/nothing, return a tuple with the new inventory and the new equiped tool"""
        db_user = self.db_user(user)
        db_user.swap_tool(inv_idx)
        db_user.save()
        await self._user_change(db_user, 'inventory', 'equiped_tool')
        return (db_user.inventory, db_user.equiped_tool)

    @queue_method
    @cache_user_method
    async def swap_stacks(self, user, idx_1, idx_2):
        """Swap two slot from the inventory, return the new inventory"""
        db_user = self.db_user(user)
        db_user.swap_stack(idx_1, idx_2)
        db_user.save()
        await self._user_change(db_user, 'inventory')
        return db_user.inventory

    @queue_method
    @cache_user_method
    async def add_xp(self, user, xp):
        """Add xp and handle level up"""
        modified, db_user = await self._add_xp(user, xp)
        await self._user_change(db_user, *modified)
        return (db_user.level, db_user.xp)

    async def _add_xp(self, db_user, xp):
        """This method also save the user so use it last, intern method used for adding xp, you must pass a db_user for the user param"""
        if not isinstance(db_user, User):
            raise Exception("Don't pass something different than a db_user to _add_xp !")
        passed_levels = db_user.add_xp(xp)
        db_user.save()
        modified = []
        if len(passed_levels) > 0:
            if db_user.inviter is not None:
                self._cache_user_before_changes(db_user.inviter.user_id)
                db_user.inviter.gems += len(passed_levels)
                db_user.inviter.save()
                await self._user_change(db_user.inviter, 'gems')
            await self.handle_level_up(db_user.user_id, passed_levels)
            modified += ['xp', 'level']
        else:
            modified.append('xp')
        return modified, db_user

    @queue_method
    @cache_user_method
    async def tool_loot(self, user, loots, xp):
        db_user = self.db_user(user)
        db_user.add_stacks(*loots)
        tool_break = db_user.tool_damage()
        if db_user.energy > 0:
            db_user.energy -= 1
        else:
            raise Exception('Activity triggered with 0 energy')
        modified, _ = await self._add_xp(db_user, xp)
        modified += ['inventory', 'equipment', 'tool', 'energy']
        await self._user_change(db_user, *modified)
        return tool_break
