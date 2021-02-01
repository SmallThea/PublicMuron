from utility.loader import narr, conf

class ChapterOutOfRangeException(Exception):
    pass

class Quest:
    name = None
    chapters_cls = None # list of chapters cls
    auto_reward = False # should the reward be given automaticaly or by interaction with panels
    hidden = False # should the quest appear in QuestPanel
    delete_on_finish = False # used by daily quest, allow to delete the trace of the quest when finished

    @property
    def chapters(self):
        return [chapter() for chapter in self.chapters_cls]

    def get_chapter(self, index):
        return self.chapters[index]

    @classmethod
    def quests(cls):
        from objects.quests.intro import IntroQuest
        basic_quests = [
            IntroQuest,
        ]
        return basic_quests + cls.success()
    
    @classmethod
    def success(cls):
        from objects.quests.sucess import SUCCESS_LIST
        return SUCCESS_LIST

    @classmethod
    def by_name(cls, name):
        """Return a quest by it's name"""
        for quest in cls.quests():
            if quest.name == name:
                return quest()
        raise Exception(f"Quest not found : {name}")

    @property
    def is_finished(self):
        pass

    @property
    def display_name(self):
        return narr(f'quests.{self.name}.name')

    @property
    def description(self):
        return narr(f'quests.{self.name}.desc')

class Chapter:
    quest_name = None
    index = None # order of the chapter in the quest line == index of the chapter in Quest.chapters
    goals = None # list of Goal objects (that are linked to hooks)
    rewards = None # dict of stuffs
    role_rewards = None # list of role_ids 

    is_place_holder = False

    @property
    def display_name(self):
        return narr(f'quests.{self.quest_name}.chapters.{self.index}.name')

    @property
    def description(self):
        return narr(f'quests.{self.quest_name}.chapters.{self.index}.desc')

    @property
    def end_description(self):
        return narr(f'quests.{self.quest_name}.chapters.{self.index}.end_desc')

    def base_advancment(self, user, module):
        advancment = []
        for goal in self.goals:
            if goal.is_to_reach:
                value = min(goal.get_value(user,module), goal.objective)
                advancment.append(value)
            else:
                advancment.append(0)
        return advancment


class UserQuest:
    quest_name = None
    chapter_index = None
    advancment = None # dict of {goal_name: values, } #TODO: replace this by a list (bevcause this is linked to goals list no need for keys)
    finished = None # indicate if the quest is done 

    def __init__(self,quest_name, chapter_index, advancment, finished):
        self.quest_name = quest_name
        self.chapter_index = chapter_index
        self.advancment = advancment
        self.finished = finished

    @property
    def display_name(self):
        return "{quest_name}┃{actual_step}/{total_steps}{can_be_finished}".format(
            quest_name=self.quest.display_name, #TODO: should we use quest name ? ==> Intro 4/5 or Inventory 4/5
            actual_step=self.chapter_index + 1,
            total_steps=len(self.quest.chapters),
            can_be_finished=self.can_be_finished and ' ✔️' or '',
        )

    @property
    def quest(self):
        return Quest.by_name(self.quest_name)

    @property
    def current_chapter(self):
        return self.quest.get_chapter(self.chapter_index)

    @property
    def active_goals(self):
        """Return a dict {advancment_index: goal_instance, } for each goals that are not finished yet"""
        goals_dict = {}
        index = -1
        for advancment, goal in zip(self.advancment ,self.current_chapter.goals):
            index += 1
            if advancment < goal.objective:
                goals_dict[index] = goal
        return goals_dict

    @property
    def active_hooks(self):
        hooks = []
        for goal in self.active_goals.values():
            for hook in goal.hooks:
                if hook not in hooks:
                    hooks.append(hook)
        return hooks

    def to_dict(self):
        return {
            'quest_name': self.quest_name,
            'chapter_index': self.chapter_index,
            'advancment': self.advancment,
            'finished': self.finished,
        }

    @classmethod
    def from_dict(cls, chapter_dict):
        return cls(**chapter_dict)

    @classmethod
    def default_quest(cls, quest_name, user, module):
        quest = Quest.by_name(quest_name)
        param_dict = {
            'quest_name': quest_name,
            'chapter_index': 0,
            'advancment': quest.get_chapter(0).base_advancment(user, module), # advancment,# [0 for _ in quest.get_chapter(0).goals],
            'finished': False,
        }
        return cls(**param_dict)

    @classmethod
    def empty_quest(cls, quest):
        # quest = Quest.by_name(quest_name)
        param_dict = {
            'quest_name': quest.name,
            'chapter_index': 0,
            'advancment': [0 for _ in quest.get_chapter(0).goals],
            'finished': False,
        }
        return cls(**param_dict)

    @property
    def can_be_finished(self):
        """Return a bool that indicate if the quest can be finished or not"""
        return (len(self.active_goals) == 0)

    def finish_chapter(self,user, module):
        if not self.can_be_finished:
            raise Exception('Try to finish a quest while all the objective are not fulfilled')
        
        self.advancment.clear()
        try:
            self.quest.get_chapter(self.chapter_index + 1)
        except IndexError: # the current chapter was the last one
            self.finished = True
        else:
            self.chapter_index += 1
            self.advancment = self.current_chapter.base_advancment(user, module)
            # FIXME: in the case a quest is finished as soon as it's get it would not be notified / earned if auto_reward


    def set_chapter(self, user, module, chapter_index):
        self.advancment.clear()
        if (chapter_index >= 0) and (chapter_index < len(self.quest.chapters)):
            self.chapter_index = chapter_index
            self.advancment = self.current_chapter.base_advancment(user, module)
        else:
            raise ChapterOutOfRangeException()


    def check_goals(self, user, quest):
        """Check the ToReach goals of a quest, to call after creating the quest or passing a chapter, can call it recursivly"""
        pass

    def trigger_hook(self, hook_name, user, module, *args, **kwargs):
        """Trigger the hook on the quest and return 3 values : 
        influence, a bool that indicate if the hook impact the quest (modify values)
        finished_chapter, if the chapter hase been finished and the reward earned
        finishable_chapter, if the chapter can be finished but is not finished
        """
        influence = False
        finished_chapter = None
        finishable_chapter = None
        for adv_index, goal in self.active_goals.items():
            if hook_name in goal.hooks:
                actual_adv = self.advancment[adv_index]
                if goal.is_to_increment:
                    incr = goal.trigger_hook(hook_name, user, module, *args, **kwargs)
                    if incr > 0:
                        influence = True
                        self.advancment[adv_index] = min(actual_adv + incr, goal.objective)
                elif goal.is_to_reach:
                    new_adv = goal.get_value(user,module)
                    if actual_adv != new_adv:
                        influence = True
                        self.advancment[adv_index] = min(new_adv, goal.objective)
        if self.can_be_finished and self.quest.auto_reward:
            finished_chapter = self.current_chapter
            self.finish_chapter(user, module)
        elif self.can_be_finished:
            finishable_chapter = self.current_chapter
                
        return influence, finished_chapter, finishable_chapter


""" """

class Goal: # == objective
    # config values
    is_to_increment = None
    is_to_reach = None

    hooks = None # hooks related to the goal

    # instance variables
    objective = None # value that determine how much we want something # 1 for ToReach

    def __init__(self, objective):
        """Initialiser the objective, can be overwrite"""
        self.objective = objective

    def format_advancment(self, advancment):
        """Can be overwrite for better display of objectifs (convert seconds to minutes for exemple)"""
        return advancment

    def format_objective(self):
        """Can be overwrite for better display of objectifs (convert seconds to minutes for exemple)"""
        return self.objective

class ToIncrement(Goal):
    is_to_increment = True
    is_to_reach = False

    def trigger_hook(self, hook_name, user, module, *args, **kwargs):
        raise Exception('This method need to be overwritten') 
        # trigger the hook and return a value that indicate how much increment objective, 0 if do nothing

class ToReach(Goal):
    is_to_increment = False
    is_to_reach = True

    def get_value(self, user, module):
        raise Exception('This method need to be overwritten')


""" Place Holder """

class PlaceHolderChapter(Chapter):
    is_place_holder = True
    
    @property
    def display_name(self):
        return narr(f'quest.panel.place_holder_title')

    @property
    def description(self):
        return narr(f'quest.panel.place_holder_desc')

    @property
    def goals(self):
        return [PlaceHolderGoal() for _ in range(20)]

class PlaceHolderGoal(ToIncrement):
    hooks = []

    def __init__(self, objective=1):
        self.objective = objective

    def trigger_hook(self, hook_name, user, module, joiner):
        return 0