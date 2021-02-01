from utility.loader import conf, narr
from objects.item import Item

# Tout les jours/semaines jours à une heure précise, les prix des grades sont réévalué selont les proportions sur le serveur !
# Grace à ce système qui baissera et augmentera les prix, le serveur gardera toujours une proportion de gens riches / pauvres raisonables.
# Tout les jours / on paie le grade, on se fait rétrograder si on a pas les sous, on peut s'auto rétrograder si on le souhaite


RANK_LIST = []

class Rank:  # TODO: faire attention, un role ne dois jamais être plus chers que l'un de ses roles supérieurs
    index = None
    needed_level = None
    # proportion des gens qui on un rank qui devrai avoir se rank ==> impacte le prix
    proportion = None
    real_proportion = None
    _allowed_tools = None
    min_rate = 0.2  # how much min we can multiply price and tax for the rank
    max_rate = 5  # how much max we can multiply price and tax for the rank

    @property
    def proportion_multiply(self):
        if self.real_proportion is None:
            return 1
        ratio = self.real_proportion/self.proportion
        ratio = max(ratio, self.min_rate)
        ratio = min(ratio, self.max_rate)
        return ratio

    @property
    def price(self):
        base_price = 250 # 50
        if self.proportion is not None:
            return int((base_price/self.proportion) * self.proportion_multiply)
        return 0

    @property
    def tax(self):
        base_tax = 5
        if self.proportion is not None:
            return int((base_tax/self.proportion) * self.proportion_multiply)
        return 0

    @property
    def display_name(self):
        return narr(f'rank.roles.{self.index}.name')

    @property
    def description(self):
        return narr(f'rank.roles.{self.index}.desc')

    @property
    def role_id(self):
        return conf(f'rank.roles.{self.index}')

    @property
    def allowed_tools(self):
        try:
            # tool_names = self.pre_rank.allowed_tools + self._allowed_tools
            return self.pre_rank.allowed_tools + [Item.by_name(name) for name in self._allowed_tools]
        except:
            # tool_names = self._allowed_tools
            return [Item.by_name(name) for name in self._allowed_tools]

        # return [Item.by_name(name) for name in tool_names]

    @property
    def gain_tools(self):
        return [Item.by_name(name) for name in self._allowed_tools]

    def loosed_tools(self):
        pass

    @property
    def pre_rank(self):
        if self.index != 0:
            return Rank.by_index(self.index-1)

    @property
    def next_rank(self):
        if self.index < (len(RANK_LIST)-1):
            return Rank.by_index(self.index+1)

    @classmethod
    def by_index(cls, index):
        for rank in RANK_LIST:
            if rank.index == index:
                return rank()
        raise Exception(f'Try to access a rank with unknown index : {index}')

    @classmethod
    def ranks(cls):
        return [rank() for rank in RANK_LIST]

    def role(self,module):
        return module.guild.get_role(self.role_id)

class Rank_0(Rank):  # base rank (free)
    index = 0
    needed_level = 0
    # price = None
    # tax = None
    proportion = None
    _allowed_tools = [f'fishing_tool_{i}' for i in range(6)]


class Rank_1(Rank):  # écuyer
    index = 1
    needed_level = 3
    # price = 100
    # tax = 10
    proportion = 50/100
    _allowed_tools = [f'mining_tool_{i}' for i in range(6)]


class Rank_2(Rank):  # guerrier
    index = 2
    needed_level = 7
    # price = 192
    # tax = 19
    proportion = 26/100
    _allowed_tools = [f'picking_tool_{i}' for i in range(6)]


class Rank_3(Rank):  # chevalier
    index = 3
    needed_level = 12
    # price = 384
    # tax = 38
    proportion = 13/100
    _allowed_tools = [f'animal_hunting_tool_{i}' for i in range(6)]


class Rank_4(Rank):  # croisé
    index = 4
    needed_level = 18
    # price = 714
    # tax = 71
    proportion = 7/100
    _allowed_tools = [f'digging_tool_{i}' for i in range(6)]


class Rank_5(Rank):  # templier
    index = 5
    needed_level = 25
    # price = 1666
    # tax = 166
    proportion = 3/100
    _allowed_tools = [f'insect_hunting_tool_{i}' for i in range(6)]


class Rank_6(Rank):  # paladin
    index = 6
    needed_level = 33
    # price = 5000
    # tax = 500
    proportion = 1/100
    _allowed_tools = [f'exploration_tool_{i}' for i in range(6)]


RANK_LIST = [
    Rank_0,
    Rank_1,
    Rank_2,
    Rank_3,
    Rank_4,
    Rank_5,
    Rank_6,
]

"""
L'ensembles des membres d'un groupe on des richesses égales. (au prix initiaux)
Exemple : tout les paladin on autant de richesse/coute autant chers que l'ensemble des écuyer ou encore des guerriers (etc..)
"""
