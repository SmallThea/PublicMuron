from utility.loader import conf, narr
from datetime import datetime,timedelta

INFRACTION_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'

def minute_to_str(minutes):
        hours = int(minutes // 60)
        minutes = int(minutes - hours * 60)
        if (hours > 0) and (minutes > 0): # minutes and hours
            return narr('protect.infraction.duration.hm').format(hours=hours,minutes=minutes)
        else:
            if hours > 0: # only hours
                return narr('protect.infraction.duration.h').format(hours=hours)
            else: # only minutes
                return narr('protect.infraction.duration.m').format(minutes=minutes)

def convert_date(date):
    if isinstance(date,str):
        return datetime.strptime(date, INFRACTION_DATE_FORMAT)
    return date.strftime(INFRACTION_DATE_FORMAT)

class Rule:
    """Represent a rule, store the punishment data and methods"""
    # config
    index = None # rule index
    sanctions = None # sanction list
    recidivism_rate = 0.2 # +20% per récidive level

    # intern
    hardness = None # how hard we want to punish (1 to 3)
    recidive = None # how much recidive

    @classmethod
    def rules(cls):
        return [
            Disrespect,
            RevealPrivate,
            BadContent,
            Discrimination,
            Spam,
            Pub,
            TimeWaster,
            Disturbing,
        ]

    @classmethod
    def by_index(cls,index):
        for rule in cls.rules():
            if rule.index == index:
                return rule()
        
        print("return the 0 index rule because they are don't all done yet")
        return cls.rules()[0]()

    @property
    def description(self):
        return narr(f'rules.{self.index}')

class Infraction:
    """Represent a infraction commit by a member"""
    rule = None # the broken rule
    hardness = None # how hard the infraction is
    recidive = None # how much recidive
    guilty = None # discord user

    def __init__(self,guilty,staff,rule_id,hardness,recidive):
        self.guilty = guilty
        self.staff = staff
        self.rule = Rule.by_index(rule_id)
        self.hardness = hardness
        self.recidive = recidive

    @property
    def place(self):
        """Return the sanction place"""
        return self.rule.sanctions[self.hardness][0]
    
    @property
    def duration(self):
        """Return the sanction duration in minutes"""
        return self.rule.sanctions[self.hardness][1]

    @property
    def final_duration(self):
        """Return the sanction duration in minutes with recidivism rate"""
        return round(self.rule.sanctions[self.hardness][1] * (1+self.recidive*self.rule.recidivism_rate))

    @property
    def sanction_info(self):
        place = narr(f'protect.infraction.place.{self.place}')
        duration_str = minute_to_str(self.final_duration)
        return narr('protect.infraction.sanction_info').format(place=place,duration=duration_str)

    @property
    def recidive_info(self):
        base_time = minute_to_str(self.duration)
        percent = round((self.recidive*self.rule.recidivism_rate)*100)
        recidive = self.recidive
        return narr('protect.infraction.recidive_info').format(base_time=base_time,percent=percent,recidive=recidive)

class InfractionRecap:
    """
    Recap of a infraction, can be stored as json for future usages

    start_date
    duration # min
    staff_id
    rule_id
    hardness
    released
    releaser_id
    """

    def __init__(self,start_date,duration,staff_id,rule_id,hardness,place,released,releaser_id):
        self.start_date = convert_date(start_date) # str to datetime
        self.duration = duration
        self.staff_id = staff_id
        self.rule_id = rule_id
        self.hardness = hardness
        self.place = place
        self.released = released
        self.releaser_id = releaser_id

    @classmethod
    def from_infraction(cls,infraction):
        """Given a infraction, return a InfractionRecap json that ca be reinstanciate later"""
        json = {
            'start_date':convert_date(datetime.now()),
            'duration':infraction.final_duration, # minutes
            'staff_id':infraction.staff.id, #TODO:
            'rule_id':infraction.rule.index,
            'hardness':infraction.hardness,
            'place':infraction.place,
            'released':False,
            'releaser_id':None,
        }
        return cls.from_json(json)
        
    @classmethod
    def from_json(cls,json):
        """Given a json, instanciate and return a InfractionRecap"""
        return cls(**json)

    def to_json(self):
        return {
            'start_date':convert_date(self.start_date),
            'duration':self.duration,
            'staff_id':self.staff_id,
            'rule_id':self.rule_id,
            'hardness':self.hardness,
            'place':self.place,
            'released':self.released,
            'releaser_id':self.releaser_id,
        }

    @property
    def active(self):
        return (self.end_date() > datetime.now()) and (not self.released)

    def recap_str(self, guilty_id):
        output = narr('protect.infraction.recap_str').format(
            guilty=f'<@!{guilty_id}>',
            staff=f'<@!{self.staff_id}>',
            rule_index=self.rule_id,
            # rule_desc=Rule.by_index(self.rule_id).description,
            hardness_word=narr(f'protect.infraction.hardness.{self.hardness}'),
            place=narr(f'protect.infraction.place.{self.place}'),
            hardness_emoji=('🟨', '🟧','🟥')[self.hardness-1],    
            time_left=self.time_left(to_str=True),
            end_date=self.end_date(to_str=True),        
        )
        if self.released:
            output += '\n'
            output += narr('protect.infraction.release_earlier').format(releaser=f'<@!{self.releaser_id}>')
        return output

    def end_date(self,to_str=False):
        minutes = timedelta(minutes=self.duration)
        final_date = self.start_date + minutes
        if to_str:
            return convert_date(final_date) # to str
        return final_date
        
    def time_left(self,to_str=False):
        """Return the time left before liberation in minute or str format if asked²"""
        time_left = self.end_date() - datetime.now()
        minutes = time_left.total_seconds() // 60
        if to_str:
            return minute_to_str(minutes)
        return minutes

    def short_str(self):
        pass

    def medium_str(self):
        pass

    def big_str(self):
        pass


class Disrespect(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class RevealPrivate(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class BadContent(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class Discrimination(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class Spam(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class Pub(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class TimeWaster(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }

class Disturbing(Rule):
    index = 0
    sanctions = {
        1:('prison',10), # 10 minutes
        2:('prison',120), # 2 hours
        3:('isolation',1440), # a day
    }