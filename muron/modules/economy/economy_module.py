import asyncio
import discord

from utility.loader import conf, narr
from bases.module_base import Module

class EconomyModule(Module):
    async def _on_ready(self):
        print("Economy run")