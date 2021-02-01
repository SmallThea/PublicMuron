from objects.item import Item
from utility.loader import narr

class Resource(Item):
    _is_resource = True
    category_name = 'resource'
    stack_size = 99

RESOURCE_LIST = []

"""
Activity
"""

class Fishing_0(Resource):
    name = 'fishing_0'
    frequency = 50000

class Fishing_1(Resource):
    name = 'fishing_1'
    frequency = 10000

class Fishing_2(Resource):
    name = 'fishing_2'
    frequency = 2500

class Fishing_3(Resource):
    name = 'fishing_3'
    frequency = 625

class Fishing_4(Resource):
    name = 'fishing_4'
    frequency = 156.25

class Fishing_5(Resource):
    name = 'fishing_5'
    frequency = 39.06

class Fishing_6(Resource):
    name = 'fishing_6'
    frequency = 9.77

class Mining_0(Resource):
    name = 'mining_0'
    frequency = 10000

class Mining_1(Resource):
    name = 'mining_1'
    frequency = 2000

class Mining_2(Resource):
    name = 'mining_2'
    frequency = 500

class Mining_3(Resource):
    name = 'mining_3'
    frequency = 125

class Mining_4(Resource):
    name = 'mining_4'
    frequency = 31.25

class Mining_5(Resource):
    name = 'mining_5'
    frequency = 7.81

class Mining_6(Resource):
    name = 'mining_6'
    frequency = 1.95

class Picking_0(Resource):
    name = 'picking_0'
    frequency = 5200

class Picking_1(Resource):
    name = 'picking_1'
    frequency = 1040

class Picking_2(Resource):
    name = 'picking_2'
    frequency = 260

class Picking_3(Resource):
    name = 'picking_3'
    frequency = 65

class Picking_4(Resource):
    name = 'picking_4'
    frequency = 16.25

class Picking_5(Resource):
    name = 'picking_5'
    frequency = 4.06

class Picking_6(Resource):
    name = 'picking_6'
    frequency = 1.02

class Animal_hunting_0(Resource):
    name = 'animal_hunting_0'
    frequency = 2600

class Animal_hunting_1(Resource):
    name = 'animal_hunting_1'
    frequency = 520

class Animal_hunting_2(Resource):
    name = 'animal_hunting_2'
    frequency = 130

class Animal_hunting_3(Resource):
    name = 'animal_hunting_3'
    frequency = 32.5

class Animal_hunting_4(Resource):
    name = 'animal_hunting_4'
    frequency = 8.12

class Animal_hunting_5(Resource):
    name = 'animal_hunting_5'
    frequency = 2.03

class Animal_hunting_6(Resource):
    name = 'animal_hunting_6'
    frequency = 0.51

class Digging_0(Resource):
    name = 'digging_0'
    frequency = 1400

class Digging_1(Resource):
    name = 'digging_1'
    frequency = 280

class Digging_2(Resource):
    name = 'digging_2'
    frequency = 70

class Digging_3(Resource):
    name = 'digging_3'
    frequency = 17.5

class Digging_4(Resource):
    name = 'digging_4'
    frequency = 4.38

class Digging_5(Resource):
    name = 'digging_5'
    frequency = 1.09

class Digging_6(Resource):
    name = 'digging_6'
    frequency = 0.27

class Insect_hunting_0(Resource):
    name = 'insect_hunting_0'
    frequency = 600

class Insect_hunting_1(Resource):
    name = 'insect_hunting_1'
    frequency = 120

class Insect_hunting_2(Resource):
    name = 'insect_hunting_2'
    frequency = 30

class Insect_hunting_3(Resource):
    name = 'insect_hunting_3'
    frequency = 7.5

class Insect_hunting_4(Resource):
    name = 'insect_hunting_4'
    frequency = 1.88

class Insect_hunting_5(Resource):
    name = 'insect_hunting_5'
    frequency = 0.47

class Insect_hunting_6(Resource):
    name = 'insect_hunting_6'
    frequency = 0.12

class Exploration_0(Resource):
    name = 'exploration_0'
    frequency = 200

class Exploration_1(Resource):
    name = 'exploration_1'
    frequency = 40

class Exploration_2(Resource):
    name = 'exploration_2'
    frequency = 10

class Exploration_3(Resource):
    name = 'exploration_3'
    frequency = 2.5

class Exploration_4(Resource):
    name = 'exploration_4'
    frequency = 0.62

class Exploration_5(Resource):
    name = 'exploration_5'
    frequency = 0.16

class Exploration_6(Resource):
    name = 'exploration_6'
    frequency = 0.04

"""
Other (gems and art)
"""

class Upgrader_0(Resource):
    name = 'upgrader_0'
    frequency = 50000

class Upgrader_1(Resource):
    name = 'upgrader_1'
    frequency = 10000

class Upgrader_2(Resource):
    name = 'upgrader_2'
    frequency = 5200

class Upgrader_3(Resource):
    name = 'upgrader_3'
    frequency = 2600

class Upgrader_4(Resource):
    name = 'upgrader_4'
    frequency = 1400

class Upgrader_5(Resource):
    name = 'upgrader_5'
    frequency = 600


#TODO: à ajouter quand il y aura une section d'outils en plus
# class Upgrader_6(Resource):
#     name = 'upgrader_6'
#     frequency = 50000




"""

"""

RESOURCE_LIST = [
    Fishing_0,
    Fishing_1,
    Fishing_2,
    Fishing_3,
    Fishing_4,
    Fishing_5,
    Fishing_6,
    Mining_0,
    Mining_1,
    Mining_2,
    Mining_3,
    Mining_4,
    Mining_5,
    Mining_6,
    Picking_0,
    Picking_1,
    Picking_2,
    Picking_3,
    Picking_4,
    Picking_5,
    Picking_6,
    Animal_hunting_0,
    Animal_hunting_1,
    Animal_hunting_2,
    Animal_hunting_3,
    Animal_hunting_4,
    Animal_hunting_5,
    Animal_hunting_6,
    Digging_0,
    Digging_1,
    Digging_2,
    Digging_3,
    Digging_4,
    Digging_5,
    Digging_6,
    Insect_hunting_0,
    Insect_hunting_1,
    Insect_hunting_2,
    Insect_hunting_3,
    Insect_hunting_4,
    Insect_hunting_5,
    Insect_hunting_6,
    Exploration_0,
    Exploration_1,
    Exploration_2,
    Exploration_3,
    Exploration_4,
    Exploration_5,
    Exploration_6,
    Upgrader_0,
    Upgrader_1,
    Upgrader_2,
    Upgrader_3,
    Upgrader_4,
    Upgrader_5,
]