import random

from objects.item import Item
from utility.loader import narr
from utility.emoji import str_to_emoji

class Recipe(Item):
    _is_recipe = True
    category_name = 'recipe'
    stack_size = 1
    result = None
    result_quantity = None
    # ingredients = None # MOVE TO THE STACK FOR SIMPLICITY dict with item_name key and quantity value
    # ingredients_frequency = None # use the result item insthead

    #generation values
    min_ingredients = 2 # le nombre minimum d'ingrédients
    max_ingredients = 5 # le nombre maximum d'ingrédients
    min_resource_level = 0 # le niveaux minimum des ressources utilisés dans la recette (inclusive)
    max_resource_level = 0 # le niveaux maximum des ressources utilisés dans la recette (inclusive)
    min_ratio_per_resource = 0.0001 # combien de % de la fréquence attendue une seul resource peut elle prendre au minimum
    max_ratio_per_resource = 0.5 # combien de % de la fréquence attendue une seul resource peut elle prendre au maximum

    @property
    def frequency(self):
        return Item.by_name(self.result).frequency * 2

    def _weighted_choice(self,items):
        weight_list = {item:item.frequency for item in items}
        summ = sum([weight for weight in weight_list.values()])
        offset = random.random()*summ
        for item,weight in weight_list.items():
            if offset < weight:
                return item
            offset -= weight

    def generate_recipe(self):
        """Generate a recip base on the generation values of the item then return a dict that contain all the ingredients"""
        desired_rarity = Item.by_name(self.result).rarity * self.result_quantity
        resource_to_use = [item() for item in Item.resources()]
        resource_to_use = resource_to_use[(self.min_resource_level)*7:(self.max_resource_level+1)*7]
        resource_to_use = [item for item in resource_to_use if (self.min_ratio_per_resource <= (item.rarity/desired_rarity) <= self.max_ratio_per_resource)]
        final_recipe = {} # key = item | value = quantity

        while desired_rarity > 0:
            if len(final_recipe) < self.max_ingredients: # use the same ingredients
                if len(final_recipe) < self.min_ingredients:
                    resource_to_use_this_turn = [item for item in resource_to_use if (item.rarity < desired_rarity) and (item not in final_recipe) ]
                else:
                    resource_to_use_this_turn = [item for item in resource_to_use if (item.rarity < desired_rarity)]

                if len(resource_to_use_this_turn) > 0:
                    if len(final_recipe) < self.max_ingredients: # ici on ne prend pas un aléatoire avec poid pour pouvoir sortir des ressources rare dans la recette
                        actual_resource = random.choice(resource_to_use_this_turn)
                    else:
                        actual_resource = self._weighted_choice(resource_to_use_this_turn) # choice(resource_to_use_this_turn)
                else:
                    actual_resource = sorted(resource_to_use, key=lambda x: x.rarity)[0]
            else:
                resource_to_use_this_turn = [item for item in final_recipe.keys() if (item.rarity < desired_rarity)]
                if len(resource_to_use_this_turn) > 0:
                    actual_resource = self._weighted_choice(resource_to_use_this_turn) # choice(resource_to_use_this_turn)
                else:
                    actual_resource = sorted(final_recipe.keys(), key=lambda x: x.rarity)[0]

            if actual_resource in final_recipe:
                final_recipe[actual_resource] += 1
            else:
                final_recipe[actual_resource] = 1
            desired_rarity -= actual_resource.rarity
        return {item.name:quantity for item,quantity in sorted(final_recipe.items(), key=lambda tup: tup[0])}

class EquipmentRecipe(Recipe):
    emoji = 'equipment_recipe'
    result_quantity = 1

    @property
    def display_name(self):
        return narr('item.equipment_recipe.name').format(item_name=Item.by_name(self.result).display_name)

    @property
    def description(self):
        return narr('item.equipment_recipe.desc').format(item_name=Item.by_name(self.result).display_name,quantity=self.result_quantity)

# dungeon conso recipe

# conso recipe

RECIPE_LIST = []

"""
Tools Recipes
"""

class FishingToolRecipe_0(EquipmentRecipe):
    name = 'fishing_tool_recipe_0'
    result = 'fishing_tool_0'
    max_resource_level = 0

class FishingToolRecipe_1(EquipmentRecipe):
    name = 'fishing_tool_recipe_1'
    result = 'fishing_tool_1'
    max_resource_level = 0

class FishingToolRecipe_2(EquipmentRecipe):
    name = 'fishing_tool_recipe_2'
    result = 'fishing_tool_2'
    max_resource_level = 0

class FishingToolRecipe_3(EquipmentRecipe):
    name = 'fishing_tool_recipe_3'
    result = 'fishing_tool_3'
    max_resource_level = 0

class FishingToolRecipe_4(EquipmentRecipe):
    name = 'fishing_tool_recipe_4'
    result = 'fishing_tool_4'
    max_resource_level = 0

class FishingToolRecipe_5(EquipmentRecipe):
    name = 'fishing_tool_recipe_5'
    result = 'fishing_tool_5'
    max_resource_level = 0


""" """

class MiningToolRecipe_0(EquipmentRecipe):
    name = 'mining_tool_recipe_0'
    result = 'mining_tool_0'
    max_resource_level = 1

class MiningToolRecipe_1(EquipmentRecipe):
    name = 'mining_tool_recipe_1'
    result = 'mining_tool_1'
    max_resource_level = 1

class MiningToolRecipe_2(EquipmentRecipe):
    name = 'mining_tool_recipe_2'
    result = 'mining_tool_2'
    max_resource_level = 1

class MiningToolRecipe_3(EquipmentRecipe):
    name = 'mining_tool_recipe_3'
    result = 'mining_tool_3'
    max_resource_level = 1

class MiningToolRecipe_4(EquipmentRecipe):
    name = 'mining_tool_recipe_4'
    result = 'mining_tool_4'
    max_resource_level = 1

class MiningToolRecipe_5(EquipmentRecipe):
    name = 'mining_tool_recipe_5'
    result = 'mining_tool_5'
    max_resource_level = 1

""" """

class PickingToolRecipe_0(EquipmentRecipe):
    name = 'picking_tool_recipe_0'
    result = 'picking_tool_0'
    max_resource_level = 2

class PickingToolRecipe_1(EquipmentRecipe):
    name = 'picking_tool_recipe_1'
    result = 'picking_tool_1'
    max_resource_level = 2

class PickingToolRecipe_2(EquipmentRecipe):
    name = 'picking_tool_recipe_2'
    result = 'picking_tool_2'
    max_resource_level = 2

class PickingToolRecipe_3(EquipmentRecipe):
    name = 'picking_tool_recipe_3'
    result = 'picking_tool_3'
    max_resource_level = 2

class PickingToolRecipe_4(EquipmentRecipe):
    name = 'picking_tool_recipe_4'
    result = 'picking_tool_4'
    max_resource_level = 2

class PickingToolRecipe_5(EquipmentRecipe):
    name = 'picking_tool_recipe_5'
    result = 'picking_tool_5'
    max_resource_level = 2

""" """

class AnimalHuntingToolRecipe_0(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_0'
    result = 'animal_hunting_tool_0'
    max_resource_level = 3

class AnimalHuntingToolRecipe_1(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_1'
    result = 'animal_hunting_tool_1'
    max_resource_level = 3

class AnimalHuntingToolRecipe_2(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_2'
    result = 'animal_hunting_tool_2'
    max_resource_level = 3

class AnimalHuntingToolRecipe_3(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_3'
    result = 'animal_hunting_tool_3'
    max_resource_level = 3

class AnimalHuntingToolRecipe_4(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_4'
    result = 'animal_hunting_tool_4'
    max_resource_level = 3

class AnimalHuntingToolRecipe_5(EquipmentRecipe):
    name = 'animal_hunting_tool_recipe_5'
    result = 'animal_hunting_tool_5'
    max_resource_level = 3

""" """

class DiggingToolRecipe_0(EquipmentRecipe):
    name = 'digging_tool_recipe_0'
    result = 'digging_tool_0'
    max_resource_level = 4

class DiggingToolRecipe_1(EquipmentRecipe):
    name = 'digging_tool_recipe_1'
    result = 'digging_tool_1'
    max_resource_level = 4

class DiggingToolRecipe_2(EquipmentRecipe):
    name = 'digging_tool_recipe_2'
    result = 'digging_tool_2'
    max_resource_level = 4

class DiggingToolRecipe_3(EquipmentRecipe):
    name = 'digging_tool_recipe_3'
    result = 'digging_tool_3'
    max_resource_level = 4

class DiggingToolRecipe_4(EquipmentRecipe):
    name = 'digging_tool_recipe_4'
    result = 'digging_tool_4'
    max_resource_level = 4

class DiggingToolRecipe_5(EquipmentRecipe):
    name = 'digging_tool_recipe_5'
    result = 'digging_tool_5'
    max_resource_level = 4

""" """

class InsectHuntingToolRecipe_0(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_0'
    result = 'insect_hunting_tool_0'
    max_resource_level = 5

class InsectHuntingToolRecipe_1(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_1'
    result = 'insect_hunting_tool_1'
    max_resource_level = 5

class InsectHuntingToolRecipe_2(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_2'
    result = 'insect_hunting_tool_2'
    max_resource_level = 5


class InsectHuntingToolRecipe_3(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_3'
    result = 'insect_hunting_tool_3'
    max_resource_level = 5

class InsectHuntingToolRecipe_4(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_4'
    result = 'insect_hunting_tool_4'
    max_resource_level = 5

class InsectHuntingToolRecipe_5(EquipmentRecipe):
    name = 'insect_hunting_tool_recipe_5'
    result = 'insect_hunting_tool_5'
    max_resource_level = 5

""" """

class ExplorationToolRecipe_0(EquipmentRecipe):
    name = 'exploration_tool_recipe_0'
    result = 'exploration_tool_0'
    max_resource_level = 6

class ExplorationToolRecipe_1(EquipmentRecipe):
    name = 'exploration_tool_recipe_1'
    result = 'exploration_tool_1'
    max_resource_level = 6

class ExplorationToolRecipe_2(EquipmentRecipe):
    name = 'exploration_tool_recipe_2'
    result = 'exploration_tool_2'
    max_resource_level = 6

class ExplorationToolRecipe_3(EquipmentRecipe):
    name = 'exploration_tool_recipe_3'
    result = 'exploration_tool_3'
    max_resource_level = 6
    
class ExplorationToolRecipe_4(EquipmentRecipe):
    name = 'exploration_tool_recipe_4'
    result = 'exploration_tool_4'
    max_resource_level = 6

class ExplorationToolRecipe_5(EquipmentRecipe):
    name = 'exploration_tool_recipe_5'
    result = 'exploration_tool_5'
    max_resource_level = 6

""" """

#TODO: necromancy

""" """


RECIPE_LIST = [
    FishingToolRecipe_0,
    FishingToolRecipe_1,
    FishingToolRecipe_2,
    FishingToolRecipe_3,
    FishingToolRecipe_4,
    FishingToolRecipe_5,
    MiningToolRecipe_0,
    MiningToolRecipe_1,
    MiningToolRecipe_2,
    MiningToolRecipe_3,
    MiningToolRecipe_4,
    MiningToolRecipe_5,
    PickingToolRecipe_0,
    PickingToolRecipe_1,
    PickingToolRecipe_2,
    PickingToolRecipe_3,
    PickingToolRecipe_4,
    PickingToolRecipe_5,
    AnimalHuntingToolRecipe_0,
    AnimalHuntingToolRecipe_1,
    AnimalHuntingToolRecipe_2,
    AnimalHuntingToolRecipe_3,
    AnimalHuntingToolRecipe_4,
    AnimalHuntingToolRecipe_5,
    DiggingToolRecipe_0,
    DiggingToolRecipe_1,
    DiggingToolRecipe_2,
    DiggingToolRecipe_3,
    DiggingToolRecipe_4,
    DiggingToolRecipe_5,
    InsectHuntingToolRecipe_0,
    InsectHuntingToolRecipe_1,
    InsectHuntingToolRecipe_2,
    InsectHuntingToolRecipe_3,
    InsectHuntingToolRecipe_4,
    InsectHuntingToolRecipe_5,
    ExplorationToolRecipe_0,
    ExplorationToolRecipe_1,
    ExplorationToolRecipe_2,
    ExplorationToolRecipe_3,
    ExplorationToolRecipe_4,
    ExplorationToolRecipe_5,
]