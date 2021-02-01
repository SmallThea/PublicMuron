
from utility.loader import conf
from objects.quest import Quest, Chapter
from objects.quests.goals import (
    ReachVocalTime,
    ReachInvite,
    ReachMoney,
    ActivityLoot,
)

class SuccessChapter(Chapter):
    index = 0
    
    @property
    def role_rewards(self):
        return [conf(f'success_roles.{self.quest_name}'),]

class Success(Quest):
    auto_reward = True
    hidden = True
    is_success = True

""" Sucess 1/16 | 24h in voc """

class Success_0_c(SuccessChapter):
    quest_name = 'success_0'
    goals = [
        ReachVocalTime(24*60*60) # 24 hours
    ]

class Success_0(Success):
    name = 'success_0'
    chapters_cls = [
        Success_0_c,
    ]

""" Sucess 2/16 | invit 25 people """

class Success_1_c(SuccessChapter):
    quest_name = 'success_1'
    goals = [
        ReachInvite(25)
    ]

class Success_1(Success):
    name = 'success_1'
    chapters_cls = [
        Success_1_c,
    ]

""" Sucess 3/16 | Reach 1 000 000  gold"""

class Success_2_c(SuccessChapter):
    quest_name = 'success_2'
    goals = [
        ReachMoney(1000000)
    ]

class Success_2(Success):
    name = 'success_2'
    chapters_cls = [
        Success_2_c,
    ]

""" Sucess 4/16 | drop fishing_6 """

class Success_3_c(SuccessChapter):
    quest_name = 'success_3'
    goals = [
        ActivityLoot(1,['fishing_6',])
    ]

class Success_3(Success):
    name = 'success_3'
    chapters_cls = [
        Success_3_c,
    ]

""" List """

SUCCESS_LIST = [
    Success_0,
    Success_1,
    Success_2,
    Success_3,
]