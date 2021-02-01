import random
from objects.item import Stack

from utility.loader import conf, narr
from objects.item import Item
from modules.activity.panels.fishing_panel import FishingPanel

from modules.activity.panels.fishing_panel import FishingPanel
from modules.activity.panels.mining_panel import MiningPanel
from modules.activity.panels.picking_panel import PickingPanel
from modules.activity.panels.animal_hunting_panel import AnimalHuntingPanel
from modules.activity.panels.digging_panel import DiggingPanel
from modules.activity.panels.insect_hunting_panel import InsectHuntingPanel
from modules.activity.panels.exploration_panel import ExplorationPanel
#TODO: necromancy

STATS = conf('stats')


class Equipment(Item):
    _is_equipment = True
    stack_size = 1
    equipment_slots = None
    upgrade_level = 0
    max_upgrade_level = 15  # also the item gain 1 stat point per level
    # nombre de point de stat de l'item au niveau 0 (répartis dans les stats aléatoires)
    base_stats_point = 5

    possible_stats = ['luck']
    max_diff_stats = 1
    # base_power = None # je ne sais plus a quoi ca sert 
    base_stats = None # indicate how much stat point each upgrade point give on a stat

    # def generate_stats_repartition(self):
    #     stats = {}
    #     allready_used = []
    #     for _ in range(self.base_stats_point):
    #         if len(allready_used) >= self.max_diff_stats:
    #             stat = random.choice(allready_used)
    #         else:
    #             stat = random.choice(self.possible_stats)
    #             if stat not in allready_used:
    #                 allready_used.append(stat)
    #         stats[stat] = stats.get(stat, 0) + 1
    #     return stats


    @property
    def recipe(self):
        """Return the recipe of the current equipment"""
        parts = self.name.split('_')
        parts.insert(len(parts) - 1 ,'recipe')
        recip_name = '_'.join(parts)
        return Item.by_name(recip_name)


""" 12 - Tools """


class Tool(Equipment):
    _is_tool = True
    equipment_slots = [12,]
    module_name = None
    max_durability = None

    @property
    def uses(self):
        return int(self.name.split('_')[-1]) + 1

    @property
    def activity_channel(self):
        return conf(f'activity.{self.module_name}')

    @property
    def loots(self):
        #FIXME: in the end change all the items names
        
        mod_name = self.module_name
        if mod_name == 'animalhunting':
            mod_name = 'animal_hunting'
        elif mod_name == 'insecthunting':
            mod_name = 'insect_hunting'

        return [f'{mod_name}_{i}' for i in range(7)]


"""
Pour les frequency des outils :
les outils auronts en fréquence ==> la fréquence de la ressource x associé a l'outil avec un multiplicateur en fonction de l'outil

x = (ressource_6 / 4) de l'outil

0 : 1 * 1024
1 : x * 256
2 : x * 64
3 : x * 16 
4 : x * 4
5 : x 

"""

FISHING_CST = 9.77 / 4
MINING_CST = 1.95 / 4
PICKING_CST = 1.02 / 4
ANIMAL_HUNTING_CST = 0.51 / 4
DIGGIN_CST = 0.27 / 4
INSECT_HUNTING_CST = 0.12 / 4
EXPLORATION_CST = 0.16 / 4

""" """

class FishingTool(Tool):
    panel = FishingPanel
    module_name = 'fishing'

class FishingTool_0(FishingTool):
    name = 'fishing_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = FISHING_CST * 1024
    base_stats = 10

class FishingTool_1(FishingTool):
    name = 'fishing_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = FISHING_CST * 256
    base_stats = 11

class FishingTool_2(FishingTool):
    name = 'fishing_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = FISHING_CST * 64
    base_stats = 12

class FishingTool_3(FishingTool):
    name = 'fishing_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = FISHING_CST * 16
    base_stats = 13

class FishingTool_4(FishingTool):
    name = 'fishing_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = FISHING_CST * 4
    base_stats = 14

class FishingTool_5(FishingTool):
    name = 'fishing_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = FISHING_CST
    base_stats = 15

""" """

class MiningTool(Tool):
    panel = MiningPanel
    module_name = 'mining'

class MiningTool_0(MiningTool):
    name = 'mining_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = MINING_CST * 1024
    base_stats = 10

class MiningTool_1(MiningTool):
    name = 'mining_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = MINING_CST * 256
    base_stats = 11

class MiningTool_2(MiningTool):
    name = 'mining_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = MINING_CST * 64
    base_stats = 12

class MiningTool_3(MiningTool):
    name = 'mining_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = MINING_CST * 16
    base_stats = 13

class MiningTool_4(MiningTool):
    name = 'mining_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = MINING_CST * 4
    base_stats = 14

class MiningTool_5(MiningTool):
    name = 'mining_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = MINING_CST
    base_stats = 15

""" """

class PickingTool(Tool):
    panel = PickingPanel
    module_name = 'picking'

class PickingTool_0(PickingTool):
    name = 'picking_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = PICKING_CST * 1024
    base_stats = 10

class PickingTool_1(PickingTool):
    name = 'picking_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = PICKING_CST * 256
    base_stats = 11

class PickingTool_2(PickingTool):
    name = 'picking_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = PICKING_CST * 64
    base_stats = 12

class PickingTool_3(PickingTool):
    name = 'picking_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = PICKING_CST * 16
    base_stats = 13

class PickingTool_4(PickingTool):
    name = 'picking_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = PICKING_CST * 4
    base_stats = 14

class PickingTool_5(PickingTool):
    name = 'picking_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = PICKING_CST
    base_stats = 15

""" """

class AnimalHuntingTool(Tool):
    panel = AnimalHuntingPanel
    module_name = 'animalhunting'

class AnimalHuntingTool_0(AnimalHuntingTool):
    name = 'animal_hunting_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = ANIMAL_HUNTING_CST * 1024
    base_stats = 10

class AnimalHuntingTool_1(AnimalHuntingTool):
    name = 'animal_hunting_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = ANIMAL_HUNTING_CST * 256
    base_stats = 11

class AnimalHuntingTool_2(AnimalHuntingTool):
    name = 'animal_hunting_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = ANIMAL_HUNTING_CST * 64
    base_stats = 12

class AnimalHuntingTool_3(AnimalHuntingTool):
    name = 'animal_hunting_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = ANIMAL_HUNTING_CST * 16
    base_stats = 13

class AnimalHuntingTool_4(AnimalHuntingTool):
    name = 'animal_hunting_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = ANIMAL_HUNTING_CST * 4
    base_stats = 14

class AnimalHuntingTool_5(AnimalHuntingTool):
    name = 'animal_hunting_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = ANIMAL_HUNTING_CST
    base_stats = 15

""" """

class DiggingTool(Tool):
    panel = DiggingPanel
    module_name = 'digging'

class DiggingTool_0(DiggingTool):
    name = 'digging_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = DIGGIN_CST * 1024
    base_stats = 10

class DiggingTool_1(DiggingTool):
    name = 'digging_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = DIGGIN_CST * 256
    base_stats = 11

class DiggingTool_2(DiggingTool):
    name = 'digging_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = DIGGIN_CST * 64
    base_stats = 12

class DiggingTool_3(DiggingTool):
    name = 'digging_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = DIGGIN_CST * 16
    base_stats = 13

class DiggingTool_4(DiggingTool):
    name = 'digging_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = DIGGIN_CST * 4
    base_stats = 14

class DiggingTool_5(DiggingTool):
    name = 'digging_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = DIGGIN_CST
    base_stats = 15

""" """

class InsectHuntingTool(Tool):
    panel = InsectHuntingPanel
    module_name = 'insecthunting'

class InsectHuntingTool_0(InsectHuntingTool):
    name = 'insect_hunting_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = INSECT_HUNTING_CST * 1024
    base_stats = 10

class InsectHuntingTool_1(InsectHuntingTool):
    name = 'insect_hunting_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = INSECT_HUNTING_CST * 256
    base_stats = 11

class InsectHuntingTool_2(InsectHuntingTool):
    name = 'insect_hunting_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = INSECT_HUNTING_CST * 64
    base_stats = 12

class InsectHuntingTool_3(InsectHuntingTool):
    name = 'insect_hunting_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = INSECT_HUNTING_CST * 16
    base_stats = 13

class InsectHuntingTool_4(InsectHuntingTool):
    name = 'insect_hunting_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = INSECT_HUNTING_CST * 4
    base_stats = 14

class InsectHuntingTool_5(InsectHuntingTool):
    name = 'insect_hunting_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = INSECT_HUNTING_CST
    base_stats = 15

""" """

class ExplorationTool(Tool):
    panel = ExplorationPanel
    module_name = 'exploration'

class ExplorationTool_0(ExplorationTool):
    name = 'exploration_tool_0'
    max_durability = 10
    efficiency = 1
    frequency = EXPLORATION_CST * 1024
    base_stats = 10

class ExplorationTool_1(ExplorationTool):
    name = 'exploration_tool_1'
    max_durability = 12
    efficiency = 2
    frequency = EXPLORATION_CST * 256
    base_stats = 11

class ExplorationTool_2(ExplorationTool):
    name = 'exploration_tool_2'
    max_durability = 14
    efficiency = 3
    frequency = EXPLORATION_CST * 64
    base_stats = 12

class ExplorationTool_3(ExplorationTool):
    name = 'exploration_tool_3'
    max_durability = 16
    efficiency = 4
    frequency = EXPLORATION_CST * 16
    base_stats = 13

class ExplorationTool_4(ExplorationTool):
    name = 'exploration_tool_4'
    max_durability = 18
    efficiency = 5
    frequency = EXPLORATION_CST * 4
    base_stats = 14

class ExplorationTool_5(ExplorationTool):
    name = 'exploration_tool_5'
    max_durability = 20
    efficiency = 6
    frequency = EXPLORATION_CST
    base_stats = 15

""" """

#TODO: necromancy


""" """

EQUIPMENT_LIST = [
    FishingTool_0,
    FishingTool_1,
    FishingTool_2,
    FishingTool_3,
    FishingTool_4,
    FishingTool_5,
    MiningTool_0,
    MiningTool_1,
    MiningTool_2,
    MiningTool_3,
    MiningTool_4,
    MiningTool_5,
    PickingTool_0,
    PickingTool_1,
    PickingTool_2,
    PickingTool_3,
    PickingTool_4,
    PickingTool_5,
    AnimalHuntingTool_0,
    AnimalHuntingTool_1,
    AnimalHuntingTool_2,
    AnimalHuntingTool_3,
    AnimalHuntingTool_4,
    AnimalHuntingTool_5,
    DiggingTool_0,
    DiggingTool_1,
    DiggingTool_2,
    DiggingTool_3,
    DiggingTool_4,
    DiggingTool_5,
    InsectHuntingTool_0,
    InsectHuntingTool_1,
    InsectHuntingTool_2,
    InsectHuntingTool_3,
    InsectHuntingTool_4,
    InsectHuntingTool_5,
    ExplorationTool_0,
    ExplorationTool_1,
    ExplorationTool_2,
    ExplorationTool_3,
    ExplorationTool_4,
    ExplorationTool_5,
]

"""Weapons"""  # 0
"""Shield"""  # 1
"""Spells"""  # 2 3 4
"""Helmets"""  # 5
"""Chestplate"""  # 6
"""Gloves"""  # 7
"""Boots"""  # 8
"""Necklace"""  # 9
"""Rings"""  # 10 11
"""Tool"""  # 12
