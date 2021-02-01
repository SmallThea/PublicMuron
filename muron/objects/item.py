"""
Différent types d'items :
- resource : item qui sont utilisé pour les crafts, non utilisable. (dent de troll, poisson clown)
- utilisable : item qui peut être utilisé une fois puis disparais (bague de mariage, fusé de détresse)
- outils : item que l'on conserve, (canne a pèche, arc, etc) ==> chance de casser à chaque utilisation | ne peut pas être utilisé dans du craft mais ne s'utilise pas (s'équipe)
- recettes : objet qui quand utilisé, conssome des ressources et créeer un object (s'achète la plupart du temps)
"""

import random
import discord
import asyncio

from utility.loader import conf, narr
from utility.emoji import str_to_emoji,emoji_bar

STATS = conf('stats')

class Item:
    name = None
    category_name = None
    stack_size = None
    frequency = None # greather mean common, smaller mean rare

    def __eq__(self, other):
        return isinstance(other,self.__class__) and (self.name == other.name)

    def __hash__(self):
        return hash(self.name) # (self.name,)
    
    def __lt__(self, other):
        self_index = self.items().index(self.__class__)
        other_index = self.items().index(other.__class__)
        return self_index < other_index

    @property
    def rarity(self):
        return 1/self.frequency 

    @property
    def sell_price(self):
        FREQUENCY_MONEY_RATIO = 100000 # un objet avec {FREQUENCY_MONEY_RATIO} frequecy vaut 1 or (en revente)
        return round(self.rarity*FREQUENCY_MONEY_RATIO)

    @property
    def buy_price(self):
        return self.sell_price*4

    @property
    def display_name(self):
        try:
            return narr(f'item.{self.name}.name')
        except:
            return "pas fait .."

    @property
    def description(self):
        try:
            return narr(f'item.{self.name}.desc')
        except:
            return "pas fait .."
        
    @property
    def emoji(self):
        return self.name# f':{self.name}:'

    @property
    def category_display_name(self):
        return narr(f'item_category.{self.category_name}')

    @property
    def category_emoji(self):
        return self.category_name

    @classmethod
    def items(cls):
        # This impact the sorting method
        from objects.items.resource import RESOURCE_LIST
        from objects.items.equipment import EQUIPMENT_LIST
        from objects.items.recipe import RECIPE_LIST
        ITEMS = RESOURCE_LIST + EQUIPMENT_LIST + RECIPE_LIST
        return ITEMS

    @classmethod
    def resources(cls):
        from objects.items.resource import RESOURCE_LIST
        return  RESOURCE_LIST

    @classmethod
    def equipments(cls):
        from objects.items.equipment import EQUIPMENT_LIST
        return  EQUIPMENT_LIST


    @classmethod
    def by_name(cls,item_name):
        for item in cls.items():#ITEMS:
            if item.name == item_name:
                return item()
        raise Exception(f'Try creating a item stack with unknown item : {item_name}')

    @classmethod
    def weighted_choice(self,items):
        """Return a random item from a list of items, using weight of items based on frequency/rarity"""
        weight_list = {item:item.frequency for item in items}
        summ = sum([weight for weight in weight_list.values()])
        offset = random.random()*summ
        for item,weight in weight_list.items():
            if offset < weight:
                return item
            offset -= weight

    @property
    def is_resource(self):
        return getattr(self, '_is_resource',False)

    @property
    def is_equipment(self):
        return getattr(self, '_is_equipment',False)

    @property
    def is_tool(self):
        return getattr(self, '_is_tool',False)

    @property
    def is_recipe(self):
        return getattr(self, '_is_recipe',False)


class Stack:
    item = None
    quantity = None

    durability = None
    recipe = None

    upgrade_level = 0
    stats_repartition = None


    @classmethod
    def to_stack_list(self,item_dict):
        """Take as parameter a dict of items {item:quantity, } then return a list of stack from this (take into account stackablity)"""
        output = []
        for item,quantity in item_dict.items():
            while quantity > 0:
                if quantity > item.stack_size:
                    output.append(Stack(item.name,item.stack_size))
                    quantity -= item.stack_size
                else:
                    output.append(Stack(item.name,quantity))
                    quantity = 0
        return sorted(output, key=lambda x: x.item)

    @classmethod
    def from_dict(self,stack_dict):
        stack = Stack(stack_dict['item_name'],stack_dict['quantity'],initialise=False)
        stack.durability = stack_dict.get('durability',None)
        stack.upgrade_level = stack_dict.get('upgrade_level',None)
        stack.stats_repartition = stack_dict.get('stats_repartition',None)
        stack.recipe = stack_dict.get('recipe',None)
        return stack

    def to_dict(self):
        stack_dict = {
            'item_name':self.item.name,
            'quantity':self.quantity
        }
        if self.item.is_tool:
            stack_dict['durability'] = self.durability
        if self.item.is_equipment:
            stack_dict['upgrade_level'] = self.upgrade_level # int from 0 to item.max_level
            stack_dict['stats_repartition'] = self.stats_repartition # dict 
        if self.item.is_recipe:
            stack_dict['recipe'] = self.recipe
        return stack_dict

    def __init__(self,item_name, quantity,initialise=True):
        self.item = Item.by_name(item_name)
        self.quantity = sorted((1,quantity,self.item.stack_size))[1] # math.clamp
        if self.item.is_tool:
            self.durability = self.item.max_durability
        if self.item.is_equipment and initialise:
            # self.stats_repartition = self.item.generate_stats_repartition()
            self.generate_base_stats()
        if self.item.is_recipe and initialise:
            self.recipe = self.item.generate_recipe()



    def __lt__(self, other):
        self_index = self.item.items().index(self.item.__class__)
        other_index = self.item.items().index(other.item.__class__)
        if self_index == other_index:
            return self.quantity > other.quantity 
            # maybe add enchantment and durability for better sorting here ! 
        return self_index < other_index

    def __eq__(self, other):
        bools = [
            self.item == other.item,
            self.quantity == other.quantity,
            self.durability == other.durability,
            self.recipe == other.recipe,
            self.upgrade_level == other.upgrade_level,
            self.stats_repartition == other.stats_repartition,
        ]
        return len([e for e in bools if not e]) == 0 # check if all elements are true

    item = None
    quantity = None

    durability = None
    recipe = None

    upgrade_level = 0
    stats_repartition = None

    @property
    def buy_price(self):
        return self.item.buy_price * self.quantity

    @property
    def sell_price(self):
        return self.item.sell_price * self.quantity

    @property
    def display_name(self):
        """Retourne le nom d'affichage de l'item (prend en compte les niveaux etc des stacks spéciaux)"""
        name = self.item.display_name
        if (self.item.is_equipment) and (self.upgrade_level > 0):
            name += f" +{self.upgrade_level}"
        return name

    def merge(self,other_stack):
        """Fill self stack with other_stack, return the remaining in Stack (can be None)"""
        if self.item.name != other_stack.item.name:
            raise Exception('Try to merge two stack of different items')
        item = self.item
        place_left = (item.stack_size - self.quantity)
        if other_stack.quantity > place_left:
            other_stack.quantity -= place_left
            self.quantity = item.stack_size
            return other_stack
        else:
            self.quantity += other_stack.quantity
            return None

    def split(self, quantity):
        """Return a tuple with 2 stack : the first have the left quantity and the second the quantity asked"""
        first = self.copy()
        splited = self.copy()
        if self.quantity <= quantity:
            raise Exception('Try to split stack with wrong quantity')

        first.quantity -= quantity
        splited.quantity = quantity
        return (first,splited)
    
    def copy(self):
        """Return a copy of the current stack, use in general for display purpouse"""
        return self.from_dict(self.to_dict())

    def short_str(self,module):
        return  "**{}×{}**".format(str_to_emoji(f':{self.item.emoji}:',module),self.quantity)

    def medium_str(self,module): # old big_str
        return f'{self.short_str(module)} ┃ {self.item.display_name}'

    def big_str(self,module):
        infos = f'*{self.item.description}*\n\n'
        if self.item.is_tool:
            bar = emoji_bar(8,self.durability/self.item.max_durability,'🟦','⬛',module)
            infos += f"{narr('durability')} : {bar} {self.durability}/{self.item.max_durability}\n"
        if self.item.is_equipment:
            stats_str = "\n".join([f"{narr(f'stats.{stat}')} +{value}" for stat,value in self.stats_modifiers.get('add',{}).items()])
            stats_str += "\n".join([f"{narr(f'stats.{stat}')} +{value*100}%" for stat,value in self.stats_modifiers.get('mult',{}).items()])
            if len(stats_str) > 0:
                infos += f"\n{stats_str}\n"

        if self.item.is_recipe:
            for item_name,quantity in self.recipe.items():
                ing_stack = Stack(item_name,quantity)
                infos += f"{ing_stack.to_str(module)}\n"
            final_stack = Stack(self.item.result,self.item.result_quantity)
            infos += f"                      {str_to_emoji(':craft_to:',module)}                \n"
            infos += f"{final_stack.to_str(module)}\n"
        
        infos +=  f"\n{narr('quantity')} : {self.quantity}/{self.item.stack_size}\n"
        infos += f"{narr('price')} : {self.sell_price} {str_to_emoji(':money:',module)}\n"
        return infos

    def to_str(self,module):
        return "{} ┃ {} **×{}**".format(str_to_emoji(f':{self.item.emoji}:',module), self.item.display_name, self.quantity)


    """ Methods only used by equipment stacks"""

    @property
    def stats_modifiers(self):
        """Return a dict with all stats and their value"""
        if not self.item.is_equipment:
            raise Exception('Try to get stats from a non equipment item')

        modifier = {}
        modifier['add'] = {}
        for stat, points in self.stats_repartition.items():
            modifier['add'][stat] = points * self.item.base_stats
        return modifier

    @property
    def upgrade_cost(self):
        """The stack needed for upgrading stuff"""
        index = int(self.item.name.split('_')[-1])
        return Stack(f'upgrader_{index}',1)
    
    @property
    def repair_cost(self):
        """Alias for upgrade_cost"""
        return self.upgrade_cost

    @property
    def is_usable(self):
        return (self.durability > 0)

    @property
    def upgrade_probability(self):
        return 1 - ((self.upgrade_level/self.item.max_upgrade_level) * 0.9)

    @property
    def is_max_level(self):
        return self.upgrade_level >= self.item.max_upgrade_level

    @property
    def is_max_durability(self):
        return self.durability >= self.item.max_durability

    def upgrade(self,quantity=1,add_upgrade_level=True):
        """Upgrade the stack and return a dict that indicate what have been upgraded"""
        if add_upgrade_level:
            self.upgrade_level += quantity

        if self.stats_repartition is None:
            self.stats_repartition = {}

        recap_dict = {}
        recap_dict['add'] = {}
        recap_dict['mult'] = {}

        allready_used = [stat for stat in self.stats_repartition.keys()]
        for _ in range(quantity):
            if len(allready_used) >= self.item.max_diff_stats:
                stat = random.choice(allready_used)
            else:
                stat = random.choice(self.item.possible_stats)
                if stat not in allready_used:
                    allready_used.append(stat)
            self.stats_repartition[stat] = self.stats_repartition.get(stat, 0) + 1
            if stat not in recap_dict['add']:
                recap_dict['add'][stat] = 0
            recap_dict['add'][stat] += self.item.base_stats

        return recap_dict

    def repair(self,quantity=1):
        self.durability = min(self.item.max_durability, self.durability + quantity)

    def generate_base_stats(self):
        self.upgrade(self.item.base_stats_point,add_upgrade_level=False)

    """ """



"""
Idées d'items :

Une bague de marriage pour se mettre en couple avec qqn
Une pierre de role, permet de créer un role temporaire customisable: version 1jour, 1semaine, 1mois 
Un sort de mutisme, lancer sur un joueur, bloque toute intéraction possible avec lui (invitations/demandes/pings/prononcer le pseudo/ etc )
Une amulette de demutisme, lancer sur un joueurs annule le mutisme
Feu de détresse (préviens les staffs)
Glaive anti-troll (kick un troll)
"""