import discord
import math

from bases.panel_base import Panel
from utility.loader import narr, conf

QUEST_PER_PAGE = 8

class QuestPanel(Panel):
    disable_delay = 120
    reset_delay_on_interact = True
    delete_on_disable = False
    one_per_user_global = True

    tracked_keys = ['quests',]
    mapping = {
        '⏪': {'callback': 'page_left', 'desc': ""},
        '◀️': {'callback': 'quest_left', 'desc': ""},
        '🟢': {'callback': 'finish_quest', 'desc': ""},
        '▶️': {'callback': 'quest_right', 'desc': ""},
        '⏩': {'callback': 'page_right', 'desc': ""},
        '✔️': {'callback': 'accept', 'desc':""},
        '❌': {'callback': 'close', 'desc':""},
    }
    base_buttons = ['⏪', '◀️', '🟢','▶️','⏩','❌']

    state = 'select_quest' # select_quest / quest_end

    finished_chapter = None
    quest_index = 0

    @property
    def total_quests(self):
        return len(self.active_quests)

    @property
    def active_quests(self):
        return [quest for quest in self.get('quests') if not (quest.quest.hidden or quest.finished)]

    @property
    def total_pages(self):
        return max(math.ceil(self.total_quests / QUEST_PER_PAGE),1)

    @property
    def actual_page(self):
        return self.quest_index // QUEST_PER_PAGE

    @property
    def current_quest(self):
        return self.active_quests[self.quest_index]

    @property
    def goals_infos(self):
        quest = self.current_quest
        chapter = quest.current_chapter

        if chapter.is_place_holder:
            return narr("in_dev")

        infos = ""
        index = -1
        for advancment, goal in zip(quest.advancment ,chapter.goals): # suposed to be linked #TODO: advancment IS A LIST (modify UserQuest)
            index += 1 # advancment is a value, goal contain the total objective, index contain the narr part
            infos += "{prefix} {goal_desc} {advancment}/{objective}\n".format(
                prefix=(advancment ==  goal.objective) and '🔹' or '🔸',
                goal_desc = narr(f'quests.{quest.quest_name}.chapters.{chapter.index}.goals')[index].format(quant=goal.format_objective()),
                advancment=goal.format_advancment(advancment),
                objective=goal.format_objective(),
            )
        return infos

    def rewards_infos(self,chapter=None):
        if chapter is None:
            quest = self.current_quest
            chapter = quest.current_chapter
    
        if chapter.is_place_holder:
            return narr("in_dev")

        infos = ""
        xp = chapter.rewards.get('xp',None)
        if xp is not None:
            infos += f"▫️ {xp} {narr('xp')}\n" #TODO: get_emoji
        money = chapter.rewards.get('money',None)
        if money is not None:
            infos += f"▫️ {money} {self.get_emoji('money')}\n"
        gems = chapter.rewards.get('gems',None)
        if gems is not None:
            infos += f"▫️ {gems} {self.get_emoji('gem')}\n"
        stacks = chapter.rewards.get('stacks',None)
        if stacks is not None:
            for stack in stacks:
                infos += f"▫️ {stack.to_str(self.module)}\n"
        return infos


    async def user_updated(self, keys):
        await self.render()

    def embed(self):
        method = getattr(self, f'{self.state}_embed')
        return method()

    def select_quest_embed(self):
        embed = discord.Embed(
            title=narr('quest.panel.title').format(actual=self.actual_page+1, total=self.total_pages),
            colour=discord.Colour.blurple(),
        )
        if self.total_quests > 0:
            desc = ""
            actual_page = self.actual_page # more optimized here
            for idx, quest in enumerate(self.active_quests):
                if idx < actual_page * QUEST_PER_PAGE:
                    continue
                if idx >= (actual_page+1) * QUEST_PER_PAGE:
                    break
                prefix = (idx == self.quest_index) and '◆' or '◇'
                desc += f"{prefix} {quest.display_name}\n"
            embed.description = desc
            
            chapter = self.current_quest.current_chapter
            embed.add_field(name=chapter.display_name,value=chapter.description,inline=False)
            embed.add_field(name=narr('quest.panel.goals'),value=self.goals_infos,inline=False)
            embed.add_field(name=narr('quest.panel.rewards'),value=self.rewards_infos(),inline=False)
        else:
            embed.description = narr('quest.panel.no_quest_desc')
        return embed

    def quest_end_embed(self):
        embed = discord.Embed(
            title=self.finished_chapter.display_name,
            colour=discord.Colour.blurple(),
            description = self.finished_chapter.end_description,
        )
        embed.add_field(
            name=narr('quest.panel.reward_end'),
            value=self.rewards_infos(self.finished_chapter),
            inline=False
            )
        return embed

    """
    Button methods
    """

    async def quest_left(self): # go up
        if self.total_quests > 0:
            self.quest_index = (self.quest_index - 1) % self.total_quests
            await self.render()

    async def quest_right(self): # go down
        if self.total_quests > 0:
            self.quest_index = (self.quest_index + 1) % self.total_quests
            await self.render()

    async def page_left(self):
        if self.total_pages > 0:
            self.quest_index = (self.quest_index // QUEST_PER_PAGE - 1 ) * QUEST_PER_PAGE # first index of the previous page
            if self.quest_index < 0:
                self.quest_index = (self.total_pages - 1) * QUEST_PER_PAGE
            await self.render()

    async def page_right(self):
        if self.total_pages > 0:
            self.quest_index = (self.quest_index // QUEST_PER_PAGE + 1 ) * QUEST_PER_PAGE # first index of the next page
            if self.quest_index >= self.total_quests:
                self.quest_index = 0
            await self.render()

    async def finish_quest(self):
        current_quest = self.current_quest
        if current_quest.can_be_finished:
            self.finished_chapter = self.current_quest.current_chapter
            self.state = 'quest_end'
            await self.module.api.finish_quest_chapter(self.user, current_quest.quest_name) # will call render automaticaly
            await self.remove_all_buttons()
            await self.add_buttons('✔️')
        else:
            self.temp_notif = narr('quest.cant_be_finished')
            await self.render()

    async def accept(self):
        self.finished_chapter = None
        self.state = 'select_quest'
        if (self.quest_index >= self.total_quests) and (self.quest_index > 0):
            self.quest_index -= 1 # if the quest is finished and it was the last one, step back for not being out of the list
        await self.render()
        await self.remove_all_buttons()
        await self.add_buttons('⏪', '◀️', '🟢','▶️','⏩','❌')

    async def close(self):
        await self.disable()