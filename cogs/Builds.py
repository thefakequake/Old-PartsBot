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

        if len(info) > 0:
            embed_msg = discord.Embed(
                title="You already have a build saved!",
                description="To update your build, do `,updatebuild (content or pcpartpicker link containing your parts)`.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return
        if list is None:
            embed_msg = discord.Embed(
                title="What would you like the contents of your Build to be?",
                description="Send your PCPartPicker link or the raw text for your build's contents.",
                timestamp=datetime.utcnow(),
                colour=red
            )
            sent_message = await ctx.send(embed=embed_msg)
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

            async with aiosqlite.connect("bot.db") as conn:
                cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)", (ctx.author.id, message.content, "https://pcpartpicker.com"))
                await conn.commit()

            embed_msg = discord.Embed(
                title="Successfully saved build",
                description="Check it out using `,build`. You can edit this build using `,updatebuild`.",
                colour=red
            )
            await ctx.send(embed=embed_msg)
            return


        urls = ['https://ae.pcpartpicker.com/list/', 'https://tr.pcpartpicker.com/list/',
                'https://th.pcpartpicker.com/list/', 'https://se.pcpartpicker.com/list/',
                'https://es.pcpartpicker.com/list/', 'https://kr.pcpartpicker.com/list/',
                'https://sg.pcpartpicker.com/list/', 'https://sa.pcpartpicker.com/list/',
                'https://qa.pcpartpicker.com/list/', 'https://pt.pcpartpicker.com/list/',
                'https://pl.pcpartpicker.com/list/', 'https://ph.pcpartpicker.com/list/',
                'https://om.pcpartpicker.com/list/', 'https://no.pcpartpicker.com/list/',
                'https://nl.pcpartpicker.com/list/', 'https://mx.pcpartpicker.com/list/',
                'https://kw.pcpartpicker.com/list/', 'https://jp.pcpartpicker.com/list/',
                'https://it.pcpartpicker.com/list/', 'https://il.pcpartpicker.com/list/',
                'https://ie.pcpartpicker.com/list/W8cdcq', 'https://in.pcpartpicker.com/list/',
                'https://hk.pcpartpicker.com/list/W8cdcq', 'https://de.pcpartpicker.com/list/',
                'https://fr.pcpartpicker.com/list/', 'https://fi.pcpartpicker.com/list/',
                'https://dk.pcpartpicker.com/list/', 'https://ca.pcpartpicker.com/list/',
                'https://br.pcpartpicker.com/list/', 'https://be.pcpartpicker.com/list/',
                'https://bh.pcpartpicker.com/list/', 'https://ar.pcpartpicker.com/list/',
                'https://pcpartpicker.com/list/',
                'https://uk.pcpartpicker.com/list/', 'https://fr.pcpartpicker.com/list/',
                'https://nz.pcpartpicker.com/list/', 'https://au.pcpartpicker.com/list/']
        iterations = 0
        matches_positions = []
        positions = []
        ctxurls = []
        for i in urls:
            if i in list:
                matches = re.finditer(i, list)
                matches_positions = [match.start() for match in matches]
            for i in matches_positions:
                positions.append(i)
            matches_positions = []
        if len(positions) > 0:
            for i in positions:
                counter = i
                while not f"{list[counter]}{list[counter + 1]}{list[counter + 2]}{list[counter + 3]}{list[counter + 4]}" == "list/":
                    counter = counter + 1
                ctxurls.append(list[positions[positions.index(i)]:(counter + 11)].replace(' ', ''))

        if len(ctxurls) > 0:

            with concurrent.futures.ThreadPoolExecutor() as pool:
                thelist = await asyncio.get_event_loop().run_in_executor(pool, format_link, ctxurls[0])

            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)",(ctx.message.author.id, thelist, ctxurls[0]))
            await conn.commit()
            await conn.close()


        else:

            if len(list) > 1950:
                list = f"{list[:1950]}..."


            conn = await aiosqlite.connect("bot.db")
            cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)",(ctx.message.author.id, list, "https://pcpartpicker.com"))
            await conn.commit()
            await conn.close()

        embed_msg = discord.Embed(title="Build Saved", description="Check it out using `,build`.", timestamp=datetime.utcnow(), colour=red)
        await ctx.send(embed=embed_msg)


    @commands.command(aliases=['buildupdate'])
    async def updatebuild(self, ctx, *, list):

        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from builds")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        foundlist = False
        for i in range(len(info)):
            if foundlist is False:
                if info[i][0] == ctx.message.author.id:
                    foundlist = True

        if foundlist is True:

            urls = ['https://ae.pcpartpicker.com/list/', 'https://tr.pcpartpicker.com/list/',
                    'https://th.pcpartpicker.com/list/', 'https://se.pcpartpicker.com/list/',
                    'https://es.pcpartpicker.com/list/', 'https://kr.pcpartpicker.com/list/',
                    'https://sg.pcpartpicker.com/list/', 'https://sa.pcpartpicker.com/list/',
                    'https://qa.pcpartpicker.com/list/', 'https://pt.pcpartpicker.com/list/',
                    'https://pl.pcpartpicker.com/list/', 'https://ph.pcpartpicker.com/list/',
                    'https://om.pcpartpicker.com/list/', 'https://no.pcpartpicker.com/list/',
                    'https://nl.pcpartpicker.com/list/', 'https://mx.pcpartpicker.com/list/',
                    'https://kw.pcpartpicker.com/list/', 'https://jp.pcpartpicker.com/list/',
                    'https://it.pcpartpicker.com/list/', 'https://il.pcpartpicker.com/list/',
                    'https://ie.pcpartpicker.com/list/W8cdcq', 'https://in.pcpartpicker.com/list/',
                    'https://hk.pcpartpicker.com/list/W8cdcq', 'https://de.pcpartpicker.com/list/',
                    'https://fr.pcpartpicker.com/list/', 'https://fi.pcpartpicker.com/list/',
                    'https://dk.pcpartpicker.com/list/', 'https://ca.pcpartpicker.com/list/',
                    'https://br.pcpartpicker.com/list/', 'https://be.pcpartpicker.com/list/',
                    'https://bh.pcpartpicker.com/list/', 'https://ar.pcpartpicker.com/list/',
                    'https://pcpartpicker.com/list/',
                    'https://uk.pcpartpicker.com/list/', 'https://fr.pcpartpicker.com/list/',
                    'https://nz.pcpartpicker.com/list/', 'https://au.pcpartpicker.com/list/']
            iterations = 0
            matches_positions = []
            positions = []
            ctxurls = []
            for i in urls:
                if i in list:
                    matches = re.finditer(i, list)
                    matches_positions = [match.start() for match in matches]
                for i in matches_positions:
                    positions.append(i)
                matches_positions = []
            if len(positions) > 0:
                for i in positions:
                    counter = i
                    while not f"{list[counter]}{list[counter + 1]}{list[counter + 2]}{list[counter + 3]}{list[counter + 4]}" == "list/":
                        counter = counter + 1
                    ctxurls.append(list[positions[positions.index(i)]:(counter + 11)].replace(' ', ''))

            if len(ctxurls) > 0:

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    thelist = await asyncio.get_event_loop().run_in_executor(pool, format_link, ctxurls[0])

                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute(f"DELETE FROM builds WHERE userid = '{ctx.message.author.id}'")
                cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)", (ctx.message.author.id, thelist, ctxurls[0]))
                await conn.commit()
                await conn.close()



            else:

                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute(f"DELETE FROM builds WHERE userid = '{ctx.message.author.id}'")
                cursor = await conn.execute("INSERT INTO builds VALUES (?, ?, ?)", (ctx.message.author.id, list, "https://pcpartpicker.com"))
                await conn.commit()
                await conn.close()

            embed_msg = discord.Embed(title="Build Updated", description="Check it out using `,build`.", timestamp=datetime.utcnow(), colour=red)
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="You don't have a build saved!", description="To create a build, do `,createbuild (content or pcpartpicker link containing your parts)`.", timestamp=datetime.utcnow(), colour=red)
            await ctx.send(embed=embed_msg)

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