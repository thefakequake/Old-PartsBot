import discord
from discord.ext import commands, tasks
from datetime import datetime
import aiosqlite
import concurrent.futures
import re
import asyncio
from utils import Member
from pypartpicker import Scraper, get_list_links
import DiscordUtils

allowed_ids = [405798011172814868, 370611001948635157, 287256464047865857, 454186048721780751, 191280151084924928, 698634807143563424, 411274336847134730, 479319375149662209, 750353117698064497, 629736214345416734, 746775313593270352]
red = discord.Colour(0x1e807c)


class Builds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["buildcreate"],
                      description="Creates a build and saves it. You can view your build or another member's build with"
                                  " the ,build command.")
    async def createbuild(self, ctx, *, _list=None):

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (ctx.author.id,))
            info = await cursor.fetchall()

        message_content = _list

        if len(info) > 0:
            embed_msg = discord.Embed(
                title="You already have a build saved!",
                description="To update your build, do `,updatebuild (content or pcpartpicker link)`.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return
        if _list is None:
            embed_msg = discord.Embed(
                title="What would you like the contents of your Build to be?",
                description="Send your PCPartPicker list link or the raw text for your build's contents.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            sent_message = await ctx.message.reply(embed=embed_msg)
            check = lambda message: message.author == ctx.author and message.content != ""
            try:
                message = await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                embed_msg = discord.Embed(
                    title="What would you like the contents of your Build to be?",
                    description="Timed out. You took too long to respond!",
                    timestamp=datetime.utcnow(),
                    colour=red
                )
                await sent_message.edit(embed=embed_msg)
                return
            message_content = message.content

        matches = get_list_links(message_content)

        build_content = message_content
        build_url = "None"
        pcpp = Scraper()

        if len(matches) > 0:
            for url in matches:
                pcpp_list = pcpp.fetch_list(url)

                description = '\n'.join([f"**{part.type}** - [{part.name}]({part.url})" if part.url != None else f"**{part.type}** - {part.name}" for part in pcpp_list.parts]) + '\n'
                if len(description) > 1950:
                    description = '\n'.join([f"**{part.type}** - {part.name}" for part in pcpp_list.parts])[:1950] + '\n'

                if description == "":
                    build_content = url
                else:
                    build_content = description

                build_url = pcpp_list.url
                break

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)", (ctx.author.id, build_content, build_url))
            await conn.commit()

        embed_msg = discord.Embed(
            title="Successfully saved build",
            description="Check it out using `,build`. You can edit this build using `,updatebuild`.",
            colour=red
        )
        await ctx.send(embed=embed_msg)
        return

    @commands.command(aliases=["buildupdate", "buildedit", "editbuild"], description="Edits your build.")
    async def updatebuild(self, ctx, *, _list=None):

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (ctx.author.id,))
            info = await cursor.fetchall()

        message_content = _list

        if len(info) == 0:
            embed_msg = discord.Embed(
                title="You don't have a build saved!",
                description="To create a build, do `,createbuild (content or pcpartpicker link)`.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return
        if _list is None:
            embed_msg = discord.Embed(
                title="What would you like the contents of your Build to be?",
                description="Send your PCPartPicker list link or the raw text for your build's contents.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            sent_message = await ctx.message.reply(embed=embed_msg)
            check = lambda message: message.author == ctx.author and message.content != ""
            try:
                message = await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                embed_msg = discord.Embed(
                    title="What would you like the contents of your Build to be?",
                    description="Timed out. You took too long to respond!",
                    timestamp=datetime.utcnow(),
                    colour=red
                )
                await sent_message.edit(embed=embed_msg)
                return
            message_content = message.content
        matches = get_list_links(message_content)

        build_content = message_content
        build_url = "None"
        pcpp = Scraper()

        if len(matches) > 0:
            for url in matches:
                pcpp_list = pcpp.fetch_list(url)

                description = '\n'.join([f"**{part.type}** - [{part.name}]({part.url})" if part.url != None else f"**{part.type}** - {part.name}" for part in pcpp_list.parts]) + '\n'
                if len(description) > 1950:
                    description = '\n'.join([f"**{part.type}** - {part.name}" for part in pcpp_list.parts])[:1950] + '\n'

                if description == "":
                    build_content = url
                else:
                    build_content = description

                build_url = pcpp_list.url
                break

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("UPDATE builds SET buildcontent = ?, pcpp = ? WHERE userid = ?", (build_content, build_url, ctx.author.id))
            await conn.commit()

        embed_msg = discord.Embed(
            title="Successfully updated build",
            description="Check it out using `,build`. You can edit this build again using `,updatebuild`.",
            colour=red
        )
        await ctx.send(embed=embed_msg)
        return

    @commands.command(description="Sends your or another member's build in chat.")
    async def build(self, ctx, *, member: Member = None):

        user = ctx.author
        if member is not None:
            user = member

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (user.id,))
            info = await cursor.fetchall()
            await conn.commit()

        if len(info) < 1:
            if member is None:
                embed_msg = discord.Embed(
                    title="You don't have a build saved!",
                    description="You can create one using the `,buildcreate` command.",
                    colour=red,
                    timestamp=datetime.utcnow()
                )
            else:
                embed_msg = discord.Embed(
                    title=f"{member.name} doesn't have a build saved!",
                    description="They can create one using the `,buildcreate` command.",
                    colour=red,
                    timestamp=datetime.utcnow()
                )
            await ctx.send(embed=embed_msg)
            return

        build = info[0]
        if build[2] == "None":
            embed_msg = discord.Embed(title=f"{user.name}'s Build", description=build[1], colour=red, timestamp=datetime.utcnow())
        else:
            embed_msg = discord.Embed(title=f"{user.name}'s Build", description=build[1], url=build[2], colour=red, timestamp=datetime.utcnow())

        await ctx.send(embed=embed_msg)

    @commands.command()
    async def addcase(self, ctx, rank, *, case_name):
        global allowed_ids

        if ctx.message.author.id in allowed_ids:
            try:
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute("INSERT INTO cases VALUES (?, ?)", (case_name, int(rank)))
                await conn.commit()
                await conn.close()
                ranks = ['High End', 'Midrange', 'Low End', 'Budget']
                embed_msg = discord.Embed(title=f"Case '{case_name}' saved as a {ranks[int(rank) - 1]}.",
                                          description="Check the `,cases` command to see the updated cases list.",
                                          timestamp=datetime.utcnow(), colour=red)
            except ValueError:
                embed_msg = discord.Embed(title=f"'{rank}' is not a number between 1 and 4!",
                                          timestamp=datetime.utcnow(), colour=red)
            except IndexError:
                embed_msg = discord.Embed(title=f"'{rank}' is not a number between 1 and 4!",
                                          timestamp=datetime.utcnow(), colour=red)
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title=f"You don't have permission to use that command!", colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command()
    async def cases(self, ctx, *, tier="None"):

        high_end_aliases = ['highend', 'high end', '1', 'top', 'he', 'best', 'high', 'tier 1', '$$$$', 'high end cases', 'highend cases']

        midrange_aliases = ['midrange', 'mid range', '2', 'tier 2', 'value', '$$$', 'mr', 'mid', 'midrange cases', 'mid range cases']

        low_end_aliases = ['lowend', 'low end', '3', 'tier 3', 'low', '$$', 'le', 'low end cases', 'lowend cases']

        budget_aliases = ['budget', 'cheapest', 'cheap', 'b', '4', '$$', 'budget cases', 'budget cases']

        if tier.lower() in high_end_aliases:
            tier = 0
        elif tier.lower() in midrange_aliases:
            tier = 1
        elif tier.lower() in low_end_aliases:
            tier = 2
        elif tier.lower() in budget_aliases:
            tier = 3

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from cases")
            info = await cursor.fetchall()
            await conn.commit()

        tiers = ['High End Cases ($$$$)', 'Midrange Cases ($$$)', 'Low End Cases ($$)', 'Budget Cases ($)']

        high_end_cases = ''
        midrange_cases = ''
        low_end_cases = ''
        budget_cases = ''

        if tier == "None":

            embeds = []

            for case in info:
                if case[1] == 1:
                    high_end_cases += f'\n{case[0]}'
                if case[1] == 2:
                    midrange_cases += f'\n{case[0]}'
                if case[1] == 3:
                    low_end_cases += f'\n{case[0]}'
                if case[1] == 4:
                    budget_cases += f'\n{case[0]}'

            descs = [high_end_cases, midrange_cases, low_end_cases, budget_cases]

            for i in range(4):
                embed_msg = discord.Embed(title=tiers[i], description=descs[i], colour=red, timestamp=datetime.utcnow())
                embed_msg.set_footer(text=f'Tier {i + 1} out of 4')
                embeds.append(embed_msg)

            paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout=30)
            paginator.add_reaction('⏪', "back")
            paginator.add_reaction('⏩', "next")
            paginator.add_reaction('❌', "delete")

            await paginator.run(embeds)
            try:
                await ctx.message.delete()
            except:
                pass

        else:

            for case in info:
                if case[1] == 1:
                    high_end_cases += f'\n{case[0]}'
                if case[1] == 2:
                    midrange_cases += f'\n{case[0]}'
                if case[1] == 3:
                    low_end_cases += f'\n{case[0]}'
                if case[1] == 4:
                    budget_cases += f'\n{case[0]}'

            descs = [i for i in (high_end_cases, midrange_cases, low_end_cases, budget_cases)]

            embed_msg = discord.Embed(title=tiers[tier], description=descs[tier], colour=red,
                                      timestamp=datetime.utcnow())
            message = await ctx.send(embed=embed_msg)

            await message.add_reaction("❌")

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) == "❌"

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check)
            except:
                embed_msg = discord.Embed(title="Timed out", colour=red)
                await ctx.send(embed=embed_msg)
                return

            await message.delete()

            try:
                await ctx.message.delete()
            except:
                pass

    @commands.command()
    async def deletecase(self, ctx, *, case_name):
        global allowed_ids

        if ctx.message.author.id in allowed_ids:
            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("SELECT * from cases")
            info = await cursor.fetchall()
            await conn.commit()
            await conn.close()

            found = False

            for case in info:
                if case[0] == case_name:
                    found = True
            if found is True:
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute(f"DELETE FROM cases WHERE name = ?", (case_name,))
                await conn.commit()
                await conn.close()
                embed_msg = discord.Embed(title=f"Deleted case '{case_name}'.", colour=red, timestamp=datetime.utcnow())
            else:
                embed_msg = discord.Embed(title=f"Case with name '{case_name}' not found.", colour=red,
                                          timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title=f"You don't have permission to use that command!", colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Builds(bot))
