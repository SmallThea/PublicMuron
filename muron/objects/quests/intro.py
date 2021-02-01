from objects.item import Stack, Item
from objects.quest import Quest, Chapter, PlaceHolderChapter
from objects.quests.goals import (
    IncrementVocalTime,
    ReachVocalTime,
    IncrementMessageSent,
    ReachMessageSent,
    IncrementMoney,
    ReachMoney,
    UseCommand,
    BuyBaseTool,
    EquipStuff,
    ActivityLoot,
    ClaimLoots,
    DesequipStuff,
    EquipStuff,
    RepairStuff,
    UpgradeStuff,
    ReachLevel,
    SellStuff,
    ReachMoney,
)

#FIXME: Only for the intro we need to make the rewards properties
#FIXME: because User has trouble importing it otherwise (circular import)

class Intro_0(Chapter): # PlaceHolderChapter
    quest_name = 'intro'
    index = 0
    goals = [
        UseCommand(1,'me'),
        IncrementMessageSent(5),
        IncrementVocalTime(5*60),
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_1(Chapter):
    quest_name = 'intro'
    index = 1
    goals = [
        BuyBaseTool(1,0),
        UseCommand(1,'inv'),
        EquipStuff(1,None,'fishing_tool_0'),
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_2(Chapter):
    quest_name = 'intro'
    index = 2
    goals = [
        IncrementVocalTime(10*60),
        ActivityLoot(2,['fishing_0',]),
        
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_3(Chapter):
    quest_name = 'intro'
    index = 3
    goals = [
        UseCommand(1,'me'),
        ClaimLoots(3,['upgrader_0',]),
        DesequipStuff(1, None, ['fishing_tool_0',]),
        RepairStuff(1,[0,]),
        UpgradeStuff(1,[0,]),
        EquipStuff(1, None, ['fishing_tool_0',]),
        UseCommand(1,'stats'),
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_4(Chapter):
    quest_name = 'intro'
    index = 4
    goals = [
        IncrementMessageSent(15),
        IncrementVocalTime(30*60),
        ActivityLoot(5,['fishing_0',]),
        ActivityLoot(1,['fishing_1',]),
        ClaimLoots(5,['upgrader_0',]),
        ReachLevel(2),
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_5(Chapter):
    quest_name = 'intro'
    index = 5
    goals = [
        SellStuff(5,['fishing_0',]),
        SellStuff(3,['upgrader_0',]),
        ReachMoney(100),
    ]
    rewards = {
        'xp':200,
        'money':25,
    }

class Intro_6(PlaceHolderChapter):
    quest_name = 'intro'
    index = 6

class IntroQuest(Quest):
    name = 'intro'
    auto_reward = False
    hidden = False
    delete_on_finish = False
    chapters_cls = [
        Intro_0,
        Intro_1,
        Intro_2,
        Intro_3,
        Intro_4,
        Intro_5,
        Intro_6,
    ]

""" 

1 ] Comment gagner de l'xp
1) Faite !me pour voir votre xp et votre level
2) Écrivez 5 messages (sans spam sinon sanction)
3) Restez 5 minutes actif dans un vocal

2] Se procurer un outil de base
1) Faites la commande !basetool et accepter l'offre
2) Faites !inv pour ouvrir votre inventaire
3) Depuis votre inventaire, équipez l'outil que vous avez acheté précédament 

3] Utiliser votre outil
1) Restez 15 mintes actif en vocal
3) Dropez 2 algue en restant en voc avec un outil équipé

4] Réparez et améliorer votre outil
1) Regardez l'énergie qu'il vous reste avec !me
2) Récupérer 3 'essence I' en utilisant la commande !claim (nécessite 2 energies)
3) Depuis votre inventaire déséquipez votre outil en utilisant ✋🏼 sur un slot vide
4) Utiliser une 'essences I' pour réparer votre outil depuis l'inventaire ('logo ...')
5) Utiliser un 'essences I' pour améliorer votre outil depuis l'inventaire ('logo marteau')
6) Rééquipez votre outil pour reprendre le farm
7) Faites !stats pour constatez votre monté en intéligence 

5] Un peux de farm
1) Envoyez 15 messages écrits (sans spam)
2) Restez 30 min en voc
3) Dropez 5 algues
4) Dropez un corail
5) Récupérez 5 'essence I' avec la commande !claim
6) Atteignez le niveaux 2

6] Gagnez de l'or
1) Depuis votre inventaire, vendez 5 algue (emoji 'billet')
2) Depuis votre inventaire vendez 2 'essence I' (emoji 'billet')
3) Atteignez les 100 d'or en vendant des objets divers (pas votre outil)

#TODO: reprendre après ici

7] Utilisation des tables
1) Allez dans le voc réservation
2) Réservez une table du poussin
3) Modifier la taille de votre table
4) Modifier le nom de votre table
5) Kickez quelqu'un de votre table

8] Un peux de farm
1) Faites 3 !claim
2) Améliorez un outil 5 fois 
3) Envoyez 20 messages (sans spam)
4) Restez 1h en vocal
5) Dropez 10 algues
6) Dropez 2 corails
7) Atteignez le niveaux 3

9] Montez en rang
1) Faites la commande !rank
2) Demandez a rank up contre de l'or 
3) Refaites la commande !basetool pour achetez votre nouvelle outil
4) Equipez votre nouvelle outil
5) Dropez un minerai  de  xxxx (activité en voc)
#TODO: ICI DONNER UNE RECETTE EN RECOMPENSES (pour la quête d'ensuite)

10] Evolution d'outil
1) Mettez un outil +15
2) Dropez une recette d'un outil de niveaux 2
3) Si la recette concorde avec  l'outil +15, utilisez la recette pour obtenir le nouvelle outil
4) Améliorez votre nouvelle outil avec une 'essence II'

11] En attente 

"""