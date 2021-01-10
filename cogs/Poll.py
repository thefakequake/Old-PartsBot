import discord
from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import typing
from emoji import UNICODE_EMOJI
import unicodedata
from random import randint, choice



red = discord.Colour.from_rgb(0, 100, 0)

class Poll(commands.Cog):

    def __init(self):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.content.lower().startswith('poll:'):
            await message.add_reaction('👍')
            await message.add_reaction('👎')

    @commands.command(description='creates a poll using all the valid emojis in your message. The emojis have to be discord default emojis and if none are put, the command just defaults to thumbs up and thumbs down.')
    async def poll(self, ctx, *, text):

            messages = text.split()

            emojis = []

            def is_emoji(s):
                count = 0
                for emoji in UNICODE_EMOJI:
                    count += s.count(emoji)
                    if count > 1:
                        return False
                return bool(count)

            message = ''

            for character in messages:
                if is_emoji(character) is True:
                    emojis.append(character)
                else:
                    message = f"{message} {character}"

            try:

                await ctx.message.delete()

            except:

                pass

            if len(emojis) > 0:
                embed_msg = discord.Embed(title=f"Poll:{message}",
                                            colour=red,
                                            timestamp=datetime.utcnow())
                embed_msg.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                send = await ctx.send(embed=embed_msg)
                try:
                    for reaction in emojis:
                        await send.add_reaction(reaction)
                except:
                    await send.add_reaction('👍')
                    await send.add_reaction('👎')
            else:
                embed_msg = discord.Embed(title=f"Poll: {message}",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
                send = await ctx.send(embed=embed_msg)
                await send.add_reaction('👍')
                await send.add_reaction('👎')
                await ctx.message.delete()

    @commands.command(description='chooses yes or no for your questions.')
    async def choice(self, ctx):
        randomchoice = randint(0, 1)

        if randomchoice == 0:
            randomchoice = 'Yes'
        else:
            randomchoice = 'No'

        embed_msg = discord.Embed(title='Choice', description=randomchoice, colour=red, timestamp=datetime.utcnow())
        await ctx.send(embed=embed_msg)


    @commands.command(description='chooses something out of your answers')
    async def multiplechoice(self, ctx, *, text):

        if ',' in text:

            items = text.split(',')
            for i in range(len(items)):
                if i == ',':
                    items.pop[i]

            embed_msg = discord.Embed(title='I choose:',
                                      description=choice(items), colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)


        else:

            embed_msg = discord.Embed(title='You need to put more than one choice!', description='Seperate your choices with commas.', colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)




def setup(bot):
    bot.add_cog(Poll(bot))