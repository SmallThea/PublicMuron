import discord
import asyncio
import datetime
from marshmallow import Schema, fields, validate

from utility.loader import narr, conf
from utility.emoji import emoji_bar, str_to_emoji
from bases.command_base import Command, UserField

from api.models.user import (
    QuestNotFoundException,
    ChapterOutOfRangeException,
)

ALLOWED = [
    conf('staff_roles.administration_leader'),
]

class SetchapterSchemas(Schema):
    user = UserField(required=True)
    quest_name = fields.Str(required=True)
    chapter_index = fields.Int(required=True,validate=validate.Range(min=0))


class SetchapterCommand(Command):
    name = 'setchapter'
    schemas = SetchapterSchemas
    args_description = {
        'user':"",
        'quest_name':"",
        'chapter_index':"",
    }
    minArgs = 3

    allowed_channels = []
    allowed_roles = [*ALLOWED]

    async def run(self):
        user = self.module.guild.get_member(self.args['user'])
        if user is None:
            return await self.cant(narr('user_not_found'))
            
        try:
            await self.module.api.set_quest_chapter(user, self.args['quest_name'],self.args['chapter_index'])
        except QuestNotFoundException:
            await self.cant(narr('setchapter_command.quest_not_found'))
        except ChapterOutOfRangeException:
            await self.cant(narr('setchapter_command.chapter_out_of_range'))
        else:
            await self.can()