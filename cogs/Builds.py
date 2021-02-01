import discord
from discord.ext import commands, tasks
from datetime import datetime
import aiosqlite
import concurrent.futures
import re
import asyncio
import requests
from bs4 import BeautifulSoup
from utils import Member
from cogs.PCPartPicker import format_pcpp_link


red = discord.Colour(0x1e807c)


class Builds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['buildcreate'])
    async def createbuild(self, ctx, *, list=None):

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (ctx.author.id,))
            info = await cursor.fetchall()

        message_content = list

        if len(info) > 0:
            embed_msg = discord.Embed(
                title="You already have a build saved!",
                description="To update your build, do `,updatebuild (content or pcpartpicker link)`.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return
        if list is None:
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

        '''
        credit to CorpNewt for this regex: https://github.com/corpnewt/CorpBot.py/blob/rewrite/Cogs/Server.py#L20
        '''
        find = re.compile(r"(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")


        matches = [match.group() for match in re.finditer(find, message_content)]

        build_content = message_content
        build_url = "None"

        if len(matches) > 0:
            for url in matches:
                if '/product/' in url:
                    continue
                if '/user/' in url:
                    continue

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    products, total_wattage, total_price, page_title = await asyncio.get_event_loop().run_in_executor(pool, format_pcpp_link, url)

                description = '\n'.join([f"**{type}** - [{name}]({url})" if url != None else f"**{type}** - {name}" for type, name, url in products])
                if len(description) > 1950:
                    description = '\n'.join([f"**{type}** - {name}" for type, name, url in products])[:1950]

                if description == "":
                    build_content = url
                else:
                    build_content = description

                build_url = url
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


    @commands.command(aliases=['buildupdate'])
    async def updatebuild(self, ctx, *, list):

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (ctx.author.id,))
            info = await cursor.fetchall()

        message_content = list

        if len(info) == 0:
            embed_msg = discord.Embed(
                title="You don't have a build saved!",
                description="To create a build, do `,createbuild (content or pcpartpicker link)`.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return
        if list is None:
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

        '''
        credit to CorpNewt for this regex: https://github.com/corpnewt/CorpBot.py/blob/rewrite/Cogs/Server.py#L20
        '''
        find = re.compile(r"(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")


        matches = [match.group() for match in re.finditer(find, message_content)]

        build_content = message_content
        build_url = "None"

        if len(matches) > 0:
            for url in matches:
                if '/product/' in url:
                    continue
                if '/user/' in url:
                    continue

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    products, total_wattage, total_price, page_title = await asyncio.get_event_loop().run_in_executor(pool, format_pcpp_link, url)

                description = '\n'.join([f"**{type}** - [{name}]({url})" if url != None else f"**{type}** - {name}" for type, name, url in products])
                if len(description) > 1950:
                    description = '\n'.join([f"**{type}** - {name}" for type, name, url in products])[:1950]

                if description == "":
                    build_content = url
                else:
                    build_content = description

                build_url = url
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


    @commands.command()
    async def build(self, ctx, *, member: Member = None):

        user = ctx.author
        if member != None:
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


    @build.error
    async def build_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            embed_msg = discord.Embed(title="Member not found", description="Is their name case sensitive? Try capitalizing their name.",
                                      timestamp=datetime.utcnow(), colour=red)
            await ctx.send(embed=embed_msg)
        print(error)

def setup(bot):
    bot.add_cog(Builds(bot))