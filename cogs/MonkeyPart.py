import discord
from discord.ext import commands, tasks

class MonkeyPart(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(MonkeyPart(bot))