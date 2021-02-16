import discord
from discord.ext import commands, tasks
from datetime import datetime
import aiosqlite
import concurrent.futures
import re
import asyncio
from utils import Member
from pypartpicker import Scraper, get_list_links


red = discord.Colour(0x1e807c)


class Builds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["buildcreate"], description="Creates a build and saves it. You can view your build or another member's build with the ,build command.")
    async def createbuild(self, ctx, *, list = None):

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

    @commands.command(aliases=["buildupdate", "buildedit", "editbuild"], description="Edit your build.")
    async def updatebuild(self, ctx, *, list=None):
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
        member = member if member else ctx.author

        async with aiosqlite.connect("bot.db") as conn:
            cursor = await conn.execute("SELECT * from builds WHERE userid IS (?)", (member.id,))
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
            embed_msg = discord.Embed(title=f"{member.name}'s Build", description=build[1], colour=red, timestamp=datetime.utcnow())
        else:
            embed_msg = discord.Embed(title=f"{member.name}'s Build", description=build[1], url=build[2], colour=red, timestamp=datetime.utcnow())

        await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Builds(bot))
