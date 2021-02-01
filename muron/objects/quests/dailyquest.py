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
)

def daily_generator():
    pass #TODO: use the date as seed for the random generator


class Daily_0(Chapter): # PlaceHolderChapter
    quest_name = 'daily'
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

class DailyQuest(Quest):
    name = 'daily'
    auto_reward = False
    hidden = False
    delete_on_finish = True
    chapters_cls = [
        Daily_0,
    ]