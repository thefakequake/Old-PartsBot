import discord
from discord.ext import commands, tasks
from datetime import datetime
import aiosqlite
import concurrent.futures
import re
import asyncio
import requests
from bs4 import BeautifulSoup

red = discord.Colour.from_rgb(0, 100, 0)

def format_link(url):
    producturls = []
    productnames = []
    producttypes = []
    newproductnames = []
    newproducttypes = []
    prices = []
    images = []
    linkfound = []

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    realtext = ''
    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()
    if not realtext == 'Verification':
        text = soup.find_all(class_='td__name')
        for a in text:
            if 'From parametric selection:' in a.get_text():
                matches = re.finditer('From parametric selection:', a.get_text())
                matches_positions = [match.start() for match in matches]
                productnames.append(a.get_text()[0:matches_positions[0]])
            else:
                if 'From parametric filter:' in a.get_text():
                    matches = re.finditer('From parametric filter:', a.get_text())
                    matches_positions = [match.start() for match in matches]
                    productnames.append(a.get_text()[0:matches_positions[0]])
                else:
                    productnames.append(a.get_text())
            if 'a href=' in str(a) and not '#view_custom_part' in str(a):
                linkfound.append(True)
                elements = str(a).split('"')
                for element in elements:
                    if element.startswith("/product/"):
                        producturls.append(f"https://pcpartpicker.com:/{element}")
            else:
                linkfound.append(False)

        text = soup.find_all(class_='td__component')
        for a in text:
            producttypes.append(a.get_text())
        text = soup.find_all(class_='td__price')
        for a in text:
            if not '-' in a.get_text():
                if 'No' in a.get_text() and 'Available' in a.get_text():
                    prices.append('No Prices Available')
                else:
                    if a.get_text().replace('\n', '').replace('Price', '') == '':
                        prices.append('No Prices Available')
                    else:
                        prices.append(a.get_text().replace('\n', '').replace('Price', ''))
        for b in range(len(producttypes)):
            stringedit = productnames[b].replace('\n', '')
            stringedit = stringedit.replace('\u200b', '')
            stringedit = stringedit.replace(
                'Note: The following custom part link was user-provided. PCPartPicker cannot vouch for its validity or safety. If you follow this link, you are doing so at your own risk.Loading...',
                '')
            newproductnames.append(stringedit)
            stringedit = producttypes[b].replace('\n', '')
            stringedit = stringedit.replace('\u200b', '')
            stringedit = stringedit.replace(
                'Note: The following custom part link was user-provided. PCPartPicker cannot vouch for its validity or safety. If you follow this link, you are doing so at your own risk.Loading...',
                '')
            stringedit = stringedit.replace('From parametric filter:', ' From parametric filter: ')
            newproducttypes.append(stringedit)
        wattage = ''
        for a in soup.find_all(class_='partlist__keyMetric'):
            wattage = a.get_text()
        wattage = wattage.replace('Estimated Wattage:', '')
        wattage = wattage.replace('\n', '')
        for img in soup.find_all('img', src=True):
            if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
                images.append(img['src'])

        for link in soup.find_all(href=True):
            if '/product/' in link['href'] and not '/product/' == link['href']:
                producturls.append(f"https://pcpartpicker.com{link['href']}")

        newproducturls = []

        falses = 0
        for i in range(len(linkfound)):
            if linkfound[i] is False:
                newproducturls.append('No URL')
                falses += 1
            else:
                newproducturls.append(producturls[i - falses])

        thelist = ''
        for i in range(len(newproductnames)):
            newline = ''
            if not thelist == '':
                newline = '\n'
            if linkfound[i] is True:
                thelist = f"{thelist}**{newline}{newproducttypes[i]}** - [{newproductnames[i]}]({newproducturls[i]})"
            else:
                thelist = f"{thelist}**{newline}{newproducttypes[i]}** - {newproductnames[i]}"
        if len(thelist) > 1950:
            thelist = ''
            for i in range(len(newproductnames)):
                newline = ''
                if not thelist == '':
                    newline = '\n'
                thelist = f"{thelist}**{newline}{newproducttypes[i]}** - {newproductnames[i]}"
            if len(thelist) > 1950:
                thelist = thelist[0:1950]
        embed_msg = discord.Embed(title=f"PCPartPicker List",
                                  description=f"{thelist}\n\n**Estimated Wattage:** {wattage}\n**Total:** {prices[-1]}",
                                  colour=red, url=url)

        pricinglist = ''

        for i in range(len(newproductnames)):
            newline = ''
            if not pricinglist == '':
                newline = '\n'
            if linkfound[i] is True:
                pricinglist = f"{pricinglist}{newline}[{newproductnames[i]}]({newproducturls[i]}) - {prices[i]}"
            else:
                pricinglist = f"{pricinglist}{newline}{newproductnames[i]} - {prices[i]}"

        if len(pricinglist) > 1950:
            pricinglist = ''
            for i in range(len(newproductnames)):
                newline = ''
                if not pricinglist == '':
                    newline = '\n'
                pricinglist = f"{pricinglist}{newline}**{newproductnames[i]}** - {prices[i]}"
            if len(pricinglist) > 1950:
                pricinglist = pricinglist[0:1950]

        return thelist

    else:
        db = open("scrapedata.txt", "w")
        db.write("0")
        global rate_limited
        rate_limited = "0"
        return "rate_limited"






class Builds(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['buildcreate'])
    async def createbuild(self, ctx, *, list):

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

        if foundlist is False:

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
        else:
            embed_msg = discord.Embed(title="You already have a build saved!", description="To update your build, do `,updatebuild (content or pcpartpicker link containing your parts)`.", timestamp=datetime.utcnow(), colour=red)
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
    async def build(self, ctx, *, member: discord.Member = None):

        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from builds")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        if not member is None:

            foundlist = False
            for i in range(len(info)):
                if foundlist is False:
                    if info[i][0] == member.id:
                        embed_msg = discord.Embed(title=f"{member.name}'s Build", description=info[i][1], url=info[i][2], colour=red, timestamp=datetime.utcnow())
                        await ctx.send(embed=embed_msg)
                        foundlist = True

            if foundlist is False:

                embed_msg = discord.Embed(title=f"{member.name} doesn't have a build saved!", colour=red, timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)

        else:

            foundlist = False
            for i in range(len(info)):
                if foundlist is False:
                    if info[i][0] == ctx.message.author.id:
                        embed_msg = discord.Embed(title=f"{ctx.message.author.name}'s Build", description=info[i][1], url=info[i][2], colour=red, timestamp=datetime.utcnow())
                        await ctx.send(embed=embed_msg)
                        foundlist = True

            if foundlist is False:

                embed_msg = discord.Embed(title="You don't have a build saved!", colour=red, timestamp=datetime.utcnow())
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