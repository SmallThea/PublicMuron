import asyncio
import random
import discord
import time

from objects.rank import Rank
from utility.loader import conf, narr

TABLE_LIST = []
SEPARATOR = '┃'


class NoMoneyException(Exception):
    pass


class NoRoleException(Exception):
    pass


class Table:
    @property
    def display_name(self):
        return narr(f'voc.tables.{self.index}.name')

    @property
    def description(self):
        return narr(f'voc.tables.{self.index}.desc')

    def base_permissions(self,owner, module):
        """Return the overwrites for the current table, can be overwriten by other table class (staff table for exemple)"""
        return {
                owner: discord.PermissionOverwrite(move_members=True, manage_channels=True),
                module.guild.get_role(conf('protect.punished_roles.prison')): discord.PermissionOverwrite(speak=False,send_messages=False,add_reactions=False),
                module.guild.get_role(conf('protect.punished_roles.isolation')): discord.PermissionOverwrite(read_messages=False),
            }

    # config var
    index = None
    price = None
    allowed_roles = None
    stats_modifier = None
    prefix = None
    can_edit_name = False
    max_size = None

    async def on_create(self, tc):
        """Can be overwriten for special actions (energy regen, ..)"""
        pass

    def can_afford(self, user, module):
        """Return a bool that indicate if a user can use this table (price, level, rank and other stuff)"""
        try:
            return self.can_afford_err(user, module)
        except:
            return False

    def can_afford_err(self, user, module):
        """Return true if the user can use this table, raise a exception instead"""

        # check roles
        if self.allowed_roles is not None:
            allowed = set(self.allowed_roles)
            actual = set([role.id for role in user.roles])
            if len(allowed-actual) == len(allowed):  # no common roles
                raise NoRoleException

        # check price
        db_user = module.api.db_user(user)
        if db_user.money < self.price:
            raise NoMoneyException

        return True

    @ classmethod
    def by_index(cls, index):
        for table in TABLE_LIST:
            if table.index == index:
                return table()
        raise Exception(f'Try to access a table with unknown index : {index}')

    @ classmethod
    def tables(cls):
        return TABLE_LIST


class TableChannel:
    """A table object with channel owner and stuff aded, reference to a channel table"""
    # intern var
    table = None
    owner = None
    module = None
    voice_channel = None

    last_activity = None

    async def is_valid(self):
        """Return a bool that indicate if the table still exist"""
        return (self in self.module.tables)

    @property
    def base_permissions(self):
        return self.table.base_permissions(self.owner,self.module)

    @classmethod
    async def create(cls, table_idx, owner, module):
        tc = cls()
        tc.table = Table.by_index(table_idx)
        tc.owner = owner
        tc.module = module

        kwargs = {
            'overwrites': tc.base_permissions,
            'category': module.category_channel,
        }

        if tc.table.max_size is not None:
            kwargs['user_limit'] = tc.table.max_size

        voice_name = f"{tc.table.prefix}{SEPARATOR}{narr('voc.creation.channel_base_name').format(name=tc.owner.display_name)}"
        tc.voice_channel = await tc.module.shared_create_voice_channel(tc.module.guild, voice_name, **kwargs)

        try:
            await tc.module.shared_move_user(tc.owner, tc.voice_channel)
        except:
            await tc.pass_empty()

        await tc.table.on_create(tc)

        return tc

    async def on_delete(self):
        """Called when the voice channel link to the table is delete"""
        self.module.tables.remove(self)
        # TODO: aactuellement appeller depuis l'éxtérieur, aussi appellé depuis l'intérieur quand on détruit le voc
        # TODO: pop la table dans la liste de table du module
        # TODO: faire certaines actions concernant les stats/boucles etc..

    async def pass_empty(self):
        """Called by module when a table is left empty, should start the timer for auto deletation"""
        self.module.loop.create_task(self.deletation_coro())

    async def pass_no_empty(self):
        """Called by module when a table is no more empty, (from 0 to 1 members)"""
        self.last_activity = time.time()

    async def deletation_coro(self):
        await asyncio.sleep(self.module.delete_delay)
        if len(self.voice_channel.members) == 0:
            if (self.last_activity is None) or (self.last_activity < (time.time() - self.module.delete_delay)):
                try:
                    await self.module.shared_delete_channel(self.voice_channel)
                except discord.errors.NotFound:
                    pass


def rank_roles(idx):
    return [rank.role_id for rank in Rank.ranks()[idx:]]
    #return [Rank.by_index(_idx).role_id for _idx in range(len(Rank.ranks()))[_idx:]  ]

class Table_rank_0(Table):
    index = 0
    price = 2
    max_size = 3
    allowed_roles = rank_roles(0)
    prefix = '🐤'

class Table_rank_1(Table):
    index = 1
    price = 5
    max_size = 5
    allowed_roles = rank_roles(1)
    prefix = '🦆'

class Table_rank_2(Table):
    index = 2
    price = 10
    max_size = 8
    allowed_roles = rank_roles(2)
    prefix = '🦉'

class Table_rank_3(Table):
    index = 3
    price = 20
    max_size = 12
    allowed_roles = rank_roles(3)
    prefix = '🐗'

class Table_rank_4(Table):
    index = 4
    price = 35
    max_size = 15
    allowed_roles = rank_roles(4)
    prefix = '🐺'

class Table_rank_5(Table):
    index = 5
    price = 83
    max_size = 18
    allowed_roles = rank_roles(5)
    prefix = '🦈'

class Table_rank_6(Table):
    index = 6
    price = 250
    max_size = 21
    allowed_roles = rank_roles(6)
    prefix = '🐲'

class Table_rank_nitro(Table):
    index = 7
    price = 10
    max_size = 10
    allowed_roles = [conf('rank.nitro_role'),]
    prefix = '💀'

class Table_energy(Table):
    index = 8
    price = 1200
    max_size = 10
    allowed_roles = None
    prefix = '⚡'

    # stats_modifier = {
    #     'add': {'luck': 10, 'wisdom': 5},
    #     'mult': {'strength': 0.5}
    # }

    energy_dt = 900  # tout les 900 secondes si il y a plus de 5 personnes dans le voc, une personne aléatoire recoit +1 énergie

    async def on_create(self, tc):
        tc.module.loop.create_task(self.energy_loop(tc))

    async def energy_loop(self, tc):
        while True:
            await asyncio.sleep(self.energy_dt)
            exist = await tc.is_valid()
            if not exist:
                return
            users = tc.voice_channel.members
            if len(users) >= 5:
                user = random.choice(users)
                await tc.module.api.add_energy(user, 1)


TABLE_LIST = [
    Table_rank_0,
    Table_rank_1,
    Table_rank_2,
    Table_rank_3,
    Table_rank_4,
    Table_rank_5,
    Table_rank_6,
    Table_rank_nitro,
    Table_energy,
]
