import math
import random
from mongoengine import *
from datetime import datetime, timedelta

from objects.item import Stack,Item
from objects.rank import Rank
from objects.rule import Infraction,InfractionRecap
from objects.quest import Quest, Chapter, UserQuest, ChapterOutOfRangeException
from utility.loader import conf

try:
    from objects.quests.intro import IntroQuest
except:
    print("Error from importing IntroQuest into user, check all the reward are properties")

STATS = conf('stats')
def XP_FUNC(level): return int(math.exp(math.sqrt(level))+800)

def default_quests():
    """Return the default quests for a new player that first join the server (success and intro)"""
    default = []
    default.append(IntroQuest)
    default += Quest.success()

    return [UserQuest.empty_quest(quest()).to_dict() for quest in default]


BANK_PER_SLOT_TAX = 250

WEAPON_SLOT = 0
SHIELD_SLOT = 1
SPELL1_SLOT = 2
SPELL2_SLOT = 3
SPELL3_SLOT = 4
HELMET_SLOT = 5
CHESTPLATE_SLOT = 6
GLOVES_SLOT = 7
BOOTS_SLOT = 8
RING1_SLOT = 9
RING2_SLOT = 10
NECKLESS_SLOT = 11
TOOL_SLOT = 12


class InventoryFullException(Exception):
    stack = None

    def __init__(self, stack=None):
        Exception.__init__(self)
        self.stack = stack

class NotEnoughtResourcesException(Exception):
    pass

class NotEnoughtEnergyException(Exception):
    missing = None

    def __init__(self, missing):
        Exception.__init__(self)
        self.missing = missing

class NotEnoughtMoneyException(Exception):
    missing = None

    def __init__(self, missing):
        Exception.__init__(self)
        self.missing = missing

class MaxLevelException(Exception):
    pass

class MaxDurabilityException(Exception):
    pass

class UpgradeFailedException(Exception):
    pass

class AllreadyBanException(Exception):
    pass

class NotAllreadyBanException(Exception):
    pass

class NoRequiredRankException(Exception):
    pass

class QuestNotFoundException(Exception):
    pass

class User(DynamicDocument):
    user_id = IntField(unique=True, required=True)  # discord id
    money = IntField(default=100)
    gems = IntField(default=0)
    inviter = ReferenceField('User', default=None)
    level = IntField(default=0)
    xp = IntField(default=0)
    energy = IntField(default=5)
    energy_max = IntField(default=5)
    _rank = IntField(default=0)  # rank index
    is_ban = BooleanField(default=False)

    # used for statistics
    message_sent = IntField(default=0)
    vocal_time = IntField(default=0)  # seconds
    join_list = ListField(DateTimeField(), default=[])
    leave_list = ListField(DateTimeField(), default=[])

    _inventory = DictField(default={})
    inventory_size = IntField(default=20) # 12

    _bank = ListField(default=[]) # infinite ordered inventory

    _equipment = DictField(default={})

    _infractions = ListField(default=[]) # [infraction_json, infraction_json] | {rule_id : [hardness, hardness, hardness],}

    _quests = ListField(default=default_quests()) # [quest_json, quest_json]

    # _market = DictField(default={})
    # market_size = IntField(default=6)

    @classmethod
    def by_id(cls, user_id, create_if_none=False):
        try:
            return cls.objects(user_id=user_id).get()
        except DoesNotExist:
            if create_if_none:
                return User(user_id=user_id).save()
            return None

    @property
    def inventory(self):
        """Return a dict of stack which represent the inventory ! this is only for display purpose, modifying stacks here don't affect the player inventory
        Exemple : {0:Stack,1:None,2:Stack} (None ==> empty stack)
        """
        inv = {}
        for idx in range(self.inventory_size):
            dict_data = self._inventory.get(str(idx), None)
            stack = Stack.from_dict(dict_data) if dict_data else None
            inv[idx] = stack
        return inv

    @property
    def empty_inventory_slots(self):
        return len({item for item in self.inventory.values() if (item is not None)})

    @property
    def equipment(self):
        """
        0 - weapon
        1 - shield
        2 - book_1
        3 - book_2
        4 - book_3
        5 - helmet 
        6 - chestplate
        7 - gloves 
        8 - boots
        9 - ring_1
        10 - ring_2
        11 - neckless
        12 - tool
        """
        equ = {}
        for idx in range(13):
            dict_data = self._equipment.get(str(idx), None)
            stack = Stack.from_dict(dict_data) if dict_data else None
            equ[idx] = stack
        return equ

    @property
    def total_invites(self):
        """return how much people have been invited by self"""
        total = 0
        for db_user in User.objects():
            inviter = db_user.inviter
            if inviter is not None:
                if inviter.user_id == self.user_id:
                    total += 1
        return total

    def total_active_invites(self, module):
        """Return how much people have been invited by self and are still on the server"""
        total = 0
        for db_user in User.objects():
            inviter = db_user.inviter
            if inviter is not None:
                if inviter.user_id == self.user_id:
                    if module.guild.get_member(db_user.user_id) is not None:
                        total += 1
        return total

    def quest_by_name(self, quest_name, give_index=False):
        """Return a UserQuest by a specific name"""
        for index, quest in enumerate(self.quests):
            if quest.quest_name == quest_name:
                if give_index:
                    return quest, index
                return quest
        return None

    def have_quest(self, quest_name):
        return self.quest_by_name(quest_name) is not None

    def add_quest(self, quest_name, d_user, module):
        if self.have_quest(quest_name):
            raise Exception('The player allready have the quest')
        quest = UserQuest.default_quest(quest_name, d_user, module)
        self._quests.append(quest.to_dict())

    def remove_quest(self, quest_name):
        out = self.quest_by_name(quest_name,give_index=True)
        if out is None:
            raise Exception('The player don\'t have the quest')
        quest, index = out
        del self._quests[index]

    def finish_quest_chapter(self, quest_name, d_user, module):
        """Finish the current chapter from the quest then return it"""
        out = self.quest_by_name(quest_name,give_index=True)

        if out is None:
            raise Exception('The player don\'t have the quest')
        
        user_quest, index = out
        finished_chapter = user_quest.current_chapter
        user_quest.finish_chapter(d_user, module) # we need theses for goal initialisation # also it can trigger quest end

        if user_quest.finished and user_quest.quest.delete_on_finish:
            del self._quests[index]
        else:
            self._quests[index] = user_quest.to_dict()
        return finished_chapter
        

    def set_quest_chapter(self, quest_name, chapter_index, d_user, module):
        out = self.quest_by_name(quest_name,give_index=True)

        if out is None:
            raise QuestNotFoundException()
        
        user_quest, index = out
        user_quest.set_chapter(d_user, module, chapter_index) # can raise errors
        if user_quest.finished and user_quest.quest.delete_on_finish:
            del self._quests[index]
        else:
            self._quests[index] = user_quest.to_dict()


    # The bank should always be sorted (for the add method)
    @property
    def bank(self):
        """Return a list of stack which represent the bank ! this is only for display purpose, modifying stacks here don't affect the player bank"""
        bank = []
        for bank_data in self._bank:
            stack = Stack.from_dict(bank_data)
            bank.append(stack)
        return bank

    @property
    def bank_tax(self):
        """Return the total bank tax to pay every day based on the number of slot in the player bank"""
        return len(self._bank) * BANK_PER_SLOT_TAX

    @property
    def quests(self):
        return [UserQuest.from_dict(quest_dict) for quest_dict in self._quests]

    @property
    def active_hooks(self):
        """Return a list of active hooks, linked to quest"""
        hooks = []
        for quest in self.quests:
            if quest.finished:
                continue
            for hook in quest.active_hooks:
                if hook not in hooks:
                    hooks.append(hook)
        return hooks

    def upgrade_equipment(self,index, quantity):
        equipment = self.inventory[index]
        if equipment.is_max_level:
            raise MaxLevelException()

        cost = equipment.upgrade_cost
        if self.have_stacks(cost):
            self.remove_stacks(cost)
            if random.random() <= equipment.upgrade_probability:
                upgrade_recap = equipment.upgrade(quantity)
                self._inventory[str(index)] = equipment.to_dict()
                return upgrade_recap
            else:
                raise UpgradeFailedException()
        else:
            raise NotEnoughtResourcesException()

    def repair_equipment(self,index, quantity):
        equipment = self.inventory[index]

        if equipment.is_max_durability:
            raise MaxDurabilityException()

        cost = equipment.repair_cost
        if self.have_stacks(cost):
            self.remove_stacks(cost)
            equipment.repair(quantity)
            self._inventory[str(index)] = equipment.to_dict()
        else:
            raise NotEnoughtResourcesException()

    def add_bank_stacks(self,*stacks):
        """Add a stack to the bank, place it in a sorted way"""
        actual_bank = self.bank
        for stack in stacks:
            inserted = False
            for index, bank_stack in enumerate(actual_bank[:]):
                if stack.item == bank_stack.item:
                    place_left = bank_stack.item.stack_size - bank_stack.quantity
                    to_move = min(place_left,stack.quantity)
                    stack.quantity -= to_move
                    bank_stack.quantity += to_move
                    if stack.quantity <= 0:
                        break
                elif bank_stack < stack: # insert
                    inserted = True
                    actual_bank.insert(index,stack)
                    break
            if (not inserted) and (stack.quantity > 0):
                actual_bank.append(stack)
        
        self._bank = [stack.to_dict() for stack in actual_bank]

    def remove_bank_stack(self,index):
        """Remove and return a stack from the bank by it index"""
        return Stack.from_dict(self._bank.pop(index))

    def get_bank_stack(self,index):
        return Stack.from_dict(self._bank[index])

    @property
    def tool(self):
        return self.equipment[TOOL_SLOT]

    @property
    def rank(self):
        return Rank.by_index(self._rank)

    @property
    def infractions(self):
        return [InfractionRecap.from_json(infraction_json) for infraction_json in self._infractions]

    @property
    def modifiers(self):
        modifiers = [
            stack.stats_modifiers for stack in self.equipment.values() if stack is not None]
        # TODO: ajouter les modifiers lié aux potions etc
        return modifiers

    @property
    def active_infraction(self):
        """Return a bool that indicate if the player has a active infraction or not"""
        for infraction in self.infractions:
            if infraction.active:
                return infraction
        return None

    @property
    def stats(self):
        """Return a dict with all stats and their value"""
        stats = {stat: 0 for stat in STATS}

        for stat in stats.keys():
            add = 0
            mult = 1
            for modifier in self.modifiers:
                add += modifier.get('add', {}).get(stat, 0)
                mult += modifier.get('mult', {}).get(stat, 0)
            stats[stat] = math.floor(add * mult)
        return stats

    def stat(self, stat_name):
        """Return a stat value based on it stat_name"""
        add = 0
        mult = 1
        for modifier in self.modifiers:
            add += modifier.get('add', {}).get(stat_name, 0)
            mult += modifier.get('mult', {}).get(stat_name, 0)
        return math.floor(add * mult)

    @property
    def claimed_loots(self):
        """Return a list of loot based on the rank of the player"""
        #TODO: prendre en compte le débordement d'inventaire avec courier

        recipes_1 = [tool.recipe for tool in self.rank.gain_tools]
        upgraders_1 = [Item.by_name(f'upgrader_{min(self.rank.index,5)}'),]

        recipes_2 = [tool.recipe for tool in self.rank.allowed_tools]
        upgraders_2 = [Item.by_name(f'upgrader_{i}') for i in range(min(self.rank.index,5)+1)]

        loots = {}

        for i in range(random.randint(3,5)): # 1 + 2-4
            recipe_list = recipes_1 if (i==0) else recipes_2
            upgrader_list = upgraders_1 if (i==0) else upgraders_2
            if (random.random() < 0.1): # 10%
                loot = Item.weighted_choice(recipe_list)
            else:
                loot = Item.weighted_choice(upgrader_list)

            if loot in loots:
                loots[loot] += 1
            else:
                loots[loot] = 1

        return Stack.to_stack_list(loots)

    def claim_loot(self):
        needed_energy = 2
        if self.energy >= needed_energy:
            stacks = self.claimed_loots
            self.energy -= needed_energy
            self.add_stacks(*stacks)
            return stacks
        else:
            raise NotEnoughtEnergyException(needed_energy - self.energy)

    def sell_stack(self, index, quantity):
        stack = self.inventory[index]
        if quantity < stack.quantity:
            remaining, to_sell = stack.split(quantity)
            self._inventory[str(index)] = remaining.to_dict()
            self.money += to_sell.sell_price
        else:
            del self._inventory[str(index)]
            self.money += stack.sell_price

    def infraction_recidive(self,rule_id):
        return len([json for json in self._infractions if json['rule_id'] == rule_id])

    def add_infraction(self,infraction):
        """Add a infraction to the player and set the liberation date for the current active infraction, return a InfractionRecap instance"""
        recap = InfractionRecap.from_infraction(infraction)
        self._infractions.append(recap.to_json())
        return recap

    def release(self, releaser_id):
        """Release the user for the current active infraction, return the concerned infraction_recap"""
        for infraction_json in self._infractions:
            infraction = InfractionRecap.from_json(infraction_json)
            if infraction.active:
                infraction_json['released'] = True
                infraction_json['releaser_id'] = releaser_id
                return InfractionRecap.from_json(infraction_json)

    def have_stacks(self, *stacks):
        quant_dict = {stack.item.name: stack.quantity for stack in stacks}
        for inv_stack in self.inventory.values():
            if inv_stack is None:
                continue
            if inv_stack.item.name in quant_dict:
                quant_dict[inv_stack.item.name] -= inv_stack.quantity
                if len([quant for quant in quant_dict.values() if quant > 0]) == 0:
                    return True
        return False

    def remove_stacks(self, *stacks):
        """Remove stacks from the inventory dict object"""
        stacks_dict = {stack.item.name: stack.quantity for stack in stacks}
        for item_name, quantity in stacks_dict.items():
            while quantity > 0:
                final_idx = None
                for idx, inv_dict in self._inventory.items():
                    if inv_dict['item_name'] == item_name:
                        if final_idx is None:
                            final_idx = idx
                        elif self._inventory[final_idx]['quantity'] > inv_dict['quantity']:
                            final_idx = idx
                inv_quant = self._inventory[final_idx]['quantity']
                if inv_quant > quantity:
                    self._inventory[final_idx]['quantity'] -= quantity
                    quantity = 0
                else:
                    del self._inventory[final_idx]
                    quantity -= inv_quant

    def pay_tax(self):
        """Pay the tax, unrank if needed, return a bool that indicate if the player get rank down"""
        unranked = False
        while True:
            if self.money >= self.rank.tax:
                self.money -= self.rank.tax
                return unranked
            else:
                unranked = True
                self._rank -= 1

    def equip(self, inv_idx, equ_idx):
        """Equipe, desequip or swap based on the bases conditions, return the what's inside the equipment slot at the end of the process"""
        inv_stack = self._inventory.get(str(inv_idx), None)
        equ_stack = self._equipment.get(str(equ_idx), None)

        to_equip = self.inventory[inv_idx]
        if to_equip is not None:
            if to_equip.item not in self.rank.allowed_tools:
                raise NoRequiredRankException()

        # safe check
        check_stack = self.inventory.get(str(inv_idx), None)
        if (check_stack is not None):
            if equ_idx not in check_stack.equipment_slots:
                raise Exception(f'Try to equip an item to a wrong slot => {self.user_id} | {inv_idx} | {equ_idx}')

        if (inv_stack is not None) and (equ_stack is not None):  # swap
            self._inventory[str(inv_idx)] = equ_stack
            self._equipment[str(equ_idx)] = inv_stack
        elif (inv_stack is not None) ^ (equ_stack is not None):
            if inv_stack is None:  # desequip
                self._inventory[str(inv_idx)] = equ_stack
                del self._equipment[str(equ_idx)]
            else:  # equip
                self._equipment[str(equ_idx)] = inv_stack
                del self._inventory[str(inv_idx)]

        return self.equipment[equ_idx]

    def desequip(self, equ_idx, inv_idx=None):
        """Desequip the current equiped tool, place it to the given inventory index, if not provided add it to inv or bank based on place left"""
        tool_stack = self.equipment[equ_idx]
        del self._equipment[str(equ_idx)]
        if inv_idx is not None:
            if str(inv_idx) in self._inventory:
                raise Exception('Try to desequip to a used inventory slot')
            self._inventory[str(inv_idx)] = tool_stack.to_dict()
        else:
            self.add_stacks(tool_stack)
            


    def use_recipe(self, inv_idx):
        recipe = self.inventory[inv_idx]
        ingredients = [Stack(item_name, quantity) for item_name, quantity in recipe.recipe.items()]
        craft = Stack(recipe.item.result, recipe.item.result_quantity)

        if not self.have_stacks(*ingredients):
            raise NotEnoughtResourcesException
        if not self.have_place_for(craft):
            have_place = False
            if recipe.quantity > 1:
                for stack in ingredients:
                    for inv_stack in self.inventory:
                        if stack.item == inv_stack.item:
                            if inv_stack.quantity <= stack.quantity:
                                have_place = True
                                break
                    if have_place:
                        break
                if not have_place:
                    raise InventoryFullException

        # remove recipe
        if self._inventory[str(inv_idx)]['quantity'] > 1:
            self._inventory[str(inv_idx)]['quantity'] -= 1
        else:
            del self._inventory[str(inv_idx)]
        self.remove_stacks(*ingredients)
        self.add_stacks(craft)

    @property
    def xp_needed(self):
        return XP_FUNC(self.level)

    def xp_needed_for(self, level):
        return XP_FUNC(level)

    def add_xp(self, xp):
        """Ajoute de l'xp en prennant en compte les monté de niveaux, renvoie une liste des niveaux passé"""
        level_passed = []
        xp += self.xp
        while xp >= self.xp_needed:
            xp -= self.xp_needed
            self.level += 1
            level_passed.append(self.level)
        self.xp = xp
        return level_passed

    def have_place_for(self, stack):
        """Return a boolean that indicate if the player have the space in his inventory for taking this stack"""
        stack_quantity = stack.quantity
        item = stack.item
        for inv_stack in self.inventory.values():
            if inv_stack is None:
                return True
            if inv_stack.item == item:
                remaining_space = (item.stack_size - inv_stack.quantity)
                stack_quantity -= remaining_space
                if stack_quantity <= 0:
                    return True
        return False

    def create_stack(self, stack):
        """Try to add a stack to a left place in the inventory, else raise InventoryFullException"""
        for idx in range(self.inventory_size):
            idx = str(idx)
            if not (idx in self._inventory):
                self._inventory[idx] = stack.to_dict()
                return
        raise InventoryFullException(stack)

    def add_stacks(self, *stacks):
        """Add multiple stacks to the inventory, create stack if needed."""
        add_to_bank = []
        for stack in stacks:
            stack_quantity = stack.quantity
            for dict_data in self._inventory.values():
                if dict_data['item_name'] == stack.item.name:
                    item = stack.item
                    place_left = item.stack_size - dict_data['quantity'] # place left in the stack
                    if place_left > 0:
                        if place_left >= stack_quantity:
                            dict_data['quantity'] += stack_quantity
                            stack_quantity = 0
                            break
                        else:
                            dict_data['quantity'] = item.stack_size
                            stack_quantity -= place_left

            if stack_quantity > 0:
                try:
                    self.create_stack(stack)
                except InventoryFullException:
                    add_to_bank.append(stack)
            
        if len(add_to_bank) > 0:
            self.add_bank_stacks(*add_to_bank)

    def swap_stack(self, idx_1, idx_2):
        """Swap two stacks, if boths stacks have same items, fill a stack with the other"""
        stack_1 = self._inventory.get(str(idx_1), None)
        stack_2 = self._inventory.get(
            str(idx_2), None)  # move stack_1 TO stack_2

        # merge two stacks if same stack
        if (stack_1 is not None) and (stack_2 is not None):
            if stack_1['item_name'] == stack_2['item_name']:
                item = Item.by_name(stack_1['item_name'])
                place_left = (item.stack_size - stack_2['quantity'])
                if stack_1['quantity'] > place_left:
                    stack_1['quantity'] -= place_left
                    stack_2['quantity'] = item.stack_size
                else:
                    stack_2['quantity'] += stack_1['quantity']
                    stack_1 = None
                return
            else:
                self._inventory[str(idx_1)] = stack_2
                self._inventory[str(idx_2)] = stack_1

        if (stack_1 is not None) ^ (stack_2 is not None):
            if stack_2 is not None:
                self._inventory[str(idx_1)] = stack_2
            else:
                del self._inventory[str(idx_1)]

            if stack_1 is not None:
                self._inventory[str(idx_2)] = stack_1
            else:
                del self._inventory[str(idx_2)]

    def send_stack(self, stack, other_user):
        """Remove the stack from self inventory and add it to other_user inventory, SAVE BOTH USER AFTER THIS OPPERATION"""
        raise Exception('NEED TO BE IMPLEMENTED')

    def tool_damage(self):
        """Remove one durabilit to the equiped tool and break it if durability reach 0, return a bool that indicate if the tool break in the process"""
        self._equipment[str(TOOL_SLOT)]['durability'] -= 1
        if self._equipment[str(TOOL_SLOT)]['durability'] <= 0:
            # del self._equipment[str(TOOL_SLOT)]
            return True # keep durability 0 items but make them not usable anymore
        return False

"""
Pouvoir ajouter ses tags sur les jeux, commande associer pour demander le tag d'un joueur sur un jeux précis ==> accepter/refuser => envoyer le tag
Un système pour rechercher des joueurs, => notification désactivable, si activé notifier quand un qqn veut jouer a un certain jeu.
"""
