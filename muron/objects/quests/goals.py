from objects.item import Stack, Item
from objects.quest import ToIncrement, ToReach

"""""""""""""""""""""""""""""""""""

            USER VARS

"""""""""""""""""""""""""""""""""""

""" VOCAL """
class IncrementVocalTime(ToIncrement):
    hooks = ['vocal_time', ]
    def trigger_hook(self, hook_name, user, module, value):
        return value

    def format_advancment(self, advancment):
        return advancment // 60

    def format_objective(self):
        return self.objective // 60

class ReachVocalTime(ToReach):
    hooks = ['vocal_time', ]
    def get_value(self, user, module):
        return module.api.db_user(user).vocal_time

    def format_advancment(self, advancment):
        return advancment // 60

    def format_objective(self):
        return self.objective // 60

""" MESSAGES """
class IncrementMessageSent(ToIncrement):
    hooks = ['message_sent', ]
    def trigger_hook(self, hook_name, user, module, value):
        return value

class ReachMessageSent(ToReach):
    hooks = ['message_sent', ]
    def get_value(self, user, module):
        return module.api.db_user(user).message_sent

""" MONEY """
class IncrementMoney(ToIncrement):
    hooks = ['money', ]
    def trigger_hook(self, hook_name, user, module, value):
        return max(0,value)

class ReachMoney(ToReach):
    hooks = ['money', ]
    def get_value(self, user, module):
        return module.api.db_user(user).money

""" LEVEL """
class IncrementLevel(ToIncrement):
    hooks = ['level', ]
    def trigger_hook(self, hook_name, user, module, value):
        return max(0,value)

class ReachLevel(ToReach):
    hooks = ['level', ]
    def get_value(self, user, module):
        return module.api.db_user(user).level

"""""""""""""""""""""""""""""""""""

            OTHERS

"""""""""""""""""""""""""""""""""""

class IncrementInvite(ToIncrement):
    """Accumulate when a member invite a other member"""
    hooks = ['invite',]
    def trigger_hook(self, hook_name, user, module, joiner): # should be trigger every minutes
        return 1

class ReachInvite(ToReach):
    hooks = ['invite',]
    def get_value(self, user, module):
        db_user = module.api.db_user(user)
        return db_user.total_active_invites(module)

class UseCommand(ToIncrement):
    # config values
    hooks = ['use_command', ]
    
    # instance vars
    command_name = None # name of the command to trigger
    params_schema = None # Marshmallow schema for validating arguments
    
    
    def __init__(self,objective,command_name, params_schema=None):
        self.objective = objective
        self.command_name = command_name
        self.params_schema = params_schema

    def trigger_hook(self, hook_name, user, module, command_name, args):
        #TODO: add schema handling
        if command_name == self.command_name:
            return 1
        return 0

class EquipStuff(ToIncrement):
    hooks = ['equip_stuff',]
    equ_slots = None
    item_names = None

    def __init__(self, objective, equ_slot=None, item_names=None): # cateogry of items | specified items list
        self.objective = objective
        self.equ_slot = equ_slot # slot to equip/desequip None for all
        self.item_names = item_names # specified items to equip/desequip

    def trigger_hook(self, hook_name, user, module, stack):
        if self.item_names is not None:
            return 1 if (stack.item.name in self.item_names) else 0
        if self.equ_slot is not None:
            return 1 if (len(set(self.equ_slot).intersection(stack.item.equipment_slots)) > 0) else 0
        return 1

class DesequipStuff(ToIncrement):
    hooks = ['desequip_stuff',]
    equ_slot = None
    item_names = None

    def __init__(self, objective, equ_slot=None, item_names=None):
        self.objective = objective
        self.equ_slot = equ_slot # slot to equip/desequip None for all
        self.item_names = item_names # specified items to equip/desequip

    def trigger_hook(self, hook_name, user, module, stack):
        if self.item_names is not None:
            return 1 if (stack.item.name in self.item_names) else 0
        if self.equ_slot is not None:
            return 1 if (len(set(self.equ_slot).intersection(stack.item.equipment_slots)) > 0) else 0
        return 1


class RepairStuff(ToIncrement):
    hooks = ['repair_stuff',]
    upgrader_indexs = None

    def __init__(self, objective, upgrader_indexs=None):
        self.objective = objective
        self.upgrader_indexs = upgrader_indexs

    def trigger_hook(self, hook_name, user, module, stack):
        if self.upgrader_indexs is None:
            return 1
        upgrader_index = int(stack.item.name.split('_')[-1])
        return 1 if (upgrader_index in self.upgrader_indexs) else 0


class UpgradeStuff(ToIncrement):
    hooks = ['upgrade_stuff',]
    upgrader_indexs = None

    def __init__(self, objective, upgrader_indexs=None):
        self.objective = objective
        self.upgrader_indexs = upgrader_indexs

    def trigger_hook(self, hook_name, user, module, stack):
        if self.upgrader_indexs is None:
            return 1
        upgrader_index = int(stack.item.name.split('_')[-1])
        return 1 if (upgrader_index in self.upgrader_indexs) else 0

class ClaimLoots(ToIncrement):
    hooks = ['claim_loots',]
    item_names = None

    def __init__(self, objective, item_names=None):
        self.objective = objective
        self.item_names = item_names

    def trigger_hook(self, hook_name, user, module, stacks):
        if self.item_names is None:
            return sum([stack.quantity for stack in stacks])
        total = 0
        for stack in stacks:
            if stack.item.name in self.item_names:
                total += stack.quantity
        return total

class SellStuff(ToIncrement):
    hooks = ['sell_stuff',]
    item_names = None

    def __init__(self, objective, item_names=None):
        self.objective = objective
        self.item_names = item_names

    def trigger_hook(self, hook_name, user, module, stack):
        if self.item_names is None:
            return stack.quantity
        if stack.item.name in self.item_names:
            return stack.quantity
        return 0

"""""""""""""""""""""""""""""""""""

        ACTIVITY RELATED

"""""""""""""""""""""""""""""""""""

class BuyBaseTool(ToIncrement):
    hooks = ['buy_base_tool',]
    base_tool_index = None # related to rank (0 for fishing 1 for mining ..)

    def __init__(self, objective, base_tool_index=None):
        self.objective = objective
        self.base_tool_index = base_tool_index

    def trigger_hook(self, hook_name, user, module, tool_index):
        if self.base_tool_index is None:
            return 1
        return 1 if (self.base_tool_index == tool_index) else 0


class ActivityLoot(ToIncrement):
    hooks = ['activity_loot',]
    item_names = None

    def __init__(self, objective, item_names=None):
        self.objective = objective
        self.item_names = item_names

    def trigger_hook(self, hook_name, user, module, stacks):
        if self.item_names is None:
            return sum([stack.quantity for stack in stacks])
        total = 0
        for stack in stacks:
            if stack.item.name in self.item_names:
                total += stack.quantity
        return total


""" """