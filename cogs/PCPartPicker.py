from bs4 import BeautifulSoup
import re
import requests
import concurrent.futures
from datetime import datetime
import discord
from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands, tasks
import asyncio
import DiscordUtils
import math
import aiosqlite
import random

global rate_limited
global allowed_ids

try:
    db = open("scrapedata.txt", "r")
    text = db.read()
    rate_limited = text
except:
    db = open("scrapedata.txt", "x")
    db = open("scrapedata.txt", "w")
    db.write("1")
    rate_limited = "1"

red = discord.Colour.from_rgb(0, 100, 0)

allowed_ids = [405798011172814868, 370611001948635157, 287256464047865857, 454186048721780751, 191280151084924928, 698634807143563424, 411274336847134730, 479319375149662209, 750353117698064497, 629736214345416734, 746775313593270352]

def query(search_term):
    try:
        session = requests.session()
        page = session.get(f"https://pcpartpicker.com/search/?q={search_term}")
        soup = BeautifulSoup(page.content, 'html.parser')
        for a in soup.find_all(class_='pageTitle'):
            realtext = a.get_text()
        if not realtext == 'Verification':
            if realtext == 'Product Search':
                text = soup.find_all(class_='search_results--link')
                productnames = []
                producturls = []
                for a in text:
                    text = a.get_text().replace('\n', '')
                    text = text.replace('\\', '\n')
                    productnames.append(text)
                for a in soup.find_all('a', href=True):
                    if (a['href'])[0:9] == '/product/':
                        producturls.append(a['href'])
                producturls = list(dict.fromkeys(producturls))
                total = 0
                for word in productnames:
                    total += len(word)
                for word in producturls:
                    total += len(word)
                if total > 1800:
                    iterate = 10
                    while total > 1800:
                        total = 0
                        iterate -= 1
                        test = productnames[0:iterate]
                        test2 = producturls[0:iterate]
                        for word in test:
                            total += len(word)
                        for word2 in test2:
                            total += len(word2)
                    return productnames[0:iterate], producturls[0:iterate]
                else:
                    return productnames[0:10], producturls[0:10]
            else: return 'use_current', realtext
        else:
            return 'rate_limited', 'rate_limited'
    except IndexError:
        return None, None




def get_specs(url, context):
    if context == 'noncustom':
        newtitles = []
        titles = []
        specs = []
        images = []
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for a in soup.find_all(class_='pageTitle'):
            realtext = a.get_text()
        if not realtext == 'Verification':

            for img in soup.find_all('img', src=True):
                if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
                    images.append(img['src'])

            for a in soup.find_all(class_='group__title'):
                text = a.get_text().replace('\n', '')
                text = text.replace('\\', '\n')
                newtitles.append(text)
            for a in soup.find_all(class_='group__content'):
                text = a.get_text().replace('\n', ' ')
                text = text.replace('\\', '\n')
                specs.append(text)

            newtitles = list(dict.fromkeys(newtitles))
            return newtitles, specs, images
        else:
            return 'rate_limited', 'rate_limited', 'rate_limited'
    else:
        newtitles = []
        titles = []
        specs = []
        images = []

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        for img in soup.find_all('img', src=True):
            if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
                images.append(img['src'])

        for a in soup.find_all(class_='pageTitle'):
            realtext = a.get_text()
        if not realtext == 'Verification':
            for a in soup.find_all(class_='group__title'):
                text = a.get_text().replace('\n', '')
                text = text.replace('\\', '\n')
                newtitles.append(text)
            for a in soup.find_all(class_='group__content'):
                text = a.get_text().replace('\n', ' ')
                text = text.replace('\\', ' ')
                specs.append(text)
            newtitles = list(dict.fromkeys(newtitles))
            return newtitles, specs, realtext, images
        else:
            return 'rate_limited', 'rate_limited', 'rate_limited', 'rate_limited'




def get_price(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()
    if not realtext == 'Verification':
        prices = []
        links = []
        sellers = []
        images = []
        stock = []

        for a in soup.find_all(class_='td__finalPrice'):
            prices.append(a.get_text().replace('\n',''))
        for a in soup.find_all('a',href=True):
            if (a['href'])[0:4] == '/mr/':
                links.append(f"https://pcpartpicker.com{a['href']}")
        for a in soup.find_all(class_="td__availability"):
            text = a.get_text().replace('\n', '')
            if text == '':
                stock.append("Out of stock")
            else:
                stock.append(text)
        for a in soup.find_all(class_='td__logo'):
            sellers.append(a.select('img')[0]['alt'].split()[0])
        for img in soup.find_all('img', src=True):
            if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
                images.append(img['src'])
        links = list(dict.fromkeys(links))
        return prices, links, sellers, images, stock
    else:
        return 'rate_limited', 'rate_limited', 'rate_limited', 'rate_limited', 'rate_limited'


def format_link(url, message):
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
            embed_msg = discord.Embed(title=f"PCPartPicker List", description=f"{thelist}\n\n**Estimated Wattage:** {wattage}\n**Total:** {prices[-1]}",
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

            embed_msg = discord.Embed(title=f"PCPartPicker List", description=f"{thelist}\n\n**Estimated Wattage:** {wattage}\n**Total:** {prices[-1]}",
                                      colour=red, url=url)

            pricing_breakdown_embed = discord.Embed(title="Pricing Breakdown", description=pricinglist, url=url, colour=red)

            return embed_msg, thelist, pricing_breakdown_embed
        else:
            db = open("scrapedata.txt", "w")
            db.write("0")
            global rate_limited
            rate_limited = "0"
            return "rate_limited", "rate_limited", "rate_limited"

async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title=f"Command '{command}' used by {str(ctx.message.author)}.", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=red, timestamp=datetime.utcnow())
    await logs.send(embed=embed_msg)


def get_build_guides(url):

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    realtext = ''

    names = []
    prices = []
    urls = []

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()

    if not realtext == 'Verification':
        for a in soup.find_all(class_='guide__title'):
            names.append(a.get_text().replace('\n', ''))

        for a in soup.find_all(class_='guide__price'):
            prices.append(a.get_text().replace('\n', ''))

        for link in soup.find_all(href=True):
            if '/guide/' in link['href'] and not link['href'] == '/guide/' and not link['href'] == 'https://pcpartpicker.com/guide/':
                urls.append(link['href'])
        return names, prices, urls
    else:
        return "rate_limited", "rate_limited", "rate_limited"


def get_build(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    realtext = ''

    productnames = []
    producttypes = []
    prices = []
    images = []

    wattage = ''

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()

    if not realtext == 'Verification':
        text = soup.find_all(class_='td__name')
        for a in text:
            if 'From parametric selection:' in a.get_text():
                matches = re.finditer('From parametric selection:', a.get_text())
                matches_positions = [match.start() for match in matches]
                productnames.append(a.get_text()[0:matches_positions[0]].replace('\n', ''))
            else:
                if 'From parametric filter:' in a.get_text():
                    matches = re.finditer('From parametric filter:', a.get_text())
                    matches_positions = [match.start() for match in matches]
                    productnames.append(a.get_text()[0:matches_positions[0]].replace('\n', ''))
                else:
                    productnames.append(a.get_text().replace('\n', ''))

        text = soup.find_all(class_='td__component')
        for a in text:
            producttypes.append(a.get_text().replace('\n', ''))

        text = soup.find_all(class_='td__price')
        for a in text:
            prices.append(a.get_text().replace('\n', ''))

        for a in soup.find_all(class_='partlist__keyMetric'):
            wattage = a.get_text()
        wattage = wattage.replace('Estimated Wattage:', '')
        wattage = wattage.replace('\n', '')

        for img in soup.find_all('img', src=True):
            if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
                images.append(img['src'])

        return productnames, producttypes, prices, images, wattage
    else:
        return "rate_limited", "rate_limited", "rate_limited", "rate_limited", "rate_limited"


def get_pcpp_subforums():
    links = []
    titles = []

    page = requests.get(f"https://pcpartpicker.com/forums/")

    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()


    if not realtext == 'Verification':


        for title in soup.find_all(class_='row--forumTitle td'):
            titles.append(title.get_text().replace('\n', ''))

        for url in soup.find_all(href=True):
            if url['href'].startswith('/forums/forum/'):
                links.append(url['href'])

        links = list(dict.fromkeys(links))
        return links, titles
    else:
        return 'rate_limited', 'rate_limited'

def get_pcpp_posts(url):

    page = requests.get(url)
    links = []
    titles = []
    description = ''
    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()

    if not realtext == 'Verification':

        for a in soup.find_all(class_='row--topicTitle td sm-align-middle'):
            for i in a.get_text():
                titles.append(a.get_text().replace('\t', '').replace('\n', '').replace('Topic', ''))

        for a in soup.find_all(href=True):
            if a['href'].startswith('/forums/topic/'):
                links.append(a['href'])


        links = list(dict.fromkeys(links))
        titles = list(dict.fromkeys(titles))
        return links, titles

    else:
        return 'rate_limited', 'rate_limited'




def get_pcpp_post(url):

    content = []
    details = []
    page = requests.get(url)

    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.find_all(class_='pageTitle'):
        realtext = a.get_text()

    if not realtext == 'Verification':

        for a in soup.find_all(class_='markdown'):
            for i in a.get_text():
                content.append(a.get_text().replace('\t', '').replace('\n', ' ').replace('\xa0', ''))
        for a in soup.find_all(class_='userName--entry'):
            details.append(a.get_text())
        content = list(dict.fromkeys(content))
        return content, details

    else:

        return 'rate_limited', 'rate_limited'


class PCPartPicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['specs', 'ps', 's'], description='shows detailed specs for a part via search query. if multiple results are returned, user must react with appropriate emoji to get the desired term.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partspecs(self, ctx, *, search_term):
        await log(self.bot, 'partspecs', ctx)
        global rate_limited
        if rate_limited == '1':
            embed_msg = discord.Embed(title=f"Finding specs for '{search_term}' on PCPartPicker...",
                                      timestamp=datetime.utcnow(), colour=red)
            message = await ctx.send(embed=embed_msg)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, search_term)
            if not productnames is None:
                if not productnames == 'rate_limited':
                    if not productnames == 'use_current':
                        if not len(productnames) == 0:
                            if not len(productnames) == 1:
                                description = ''
                                for i in range(0, len(productnames)):
                                    if description == '':
                                        description = f"{i + 1}. [{productnames[i]}]({'https://pcpartpicker.com' + producturls[i]})"
                                    else:
                                        description = f"{description}\n{i + 1}. [{productnames[i]}]({'https://pcpartpicker.com' + producturls[i]})"
                                embed_msg = discord.Embed(title=f"Showing results for {search_term}:",
                                                          description=description, colour=red,
                                                          timestamp=datetime.utcnow())
                                await message.edit(embed=embed_msg)
                                one = "1\N{variation selector-16}\N{combining enclosing keycap}"
                                two = "2\N{variation selector-16}\N{combining enclosing keycap}"
                                three = "3\N{variation selector-16}\N{combining enclosing keycap}"
                                four = "4\N{variation selector-16}\N{combining enclosing keycap}"
                                five = "5\N{variation selector-16}\N{combining enclosing keycap}"
                                six = "6\N{variation selector-16}\N{combining enclosing keycap}"
                                seven = "7\N{variation selector-16}\N{combining enclosing keycap}"
                                eight = "8\N{variation selector-16}\N{combining enclosing keycap}"
                                nine = "9\N{variation selector-16}\N{combining enclosing keycap}"
                                ten = "\N{keycap ten}"
                                ex = "\u274C"
                                reactions = []
                                iterate = 0
                                for r in (one, two, three, four, five, six, seven, eight, nine, ten):
                                    iterate = iterate + 1
                                    if not iterate > len(producturls):
                                        await message.add_reaction(r)
                                        reactions.append(r)
                                await message.add_reaction(ex)
                                reactions.append(ex)

                                def check(reaction, user):
                                    return user == ctx.message.author and str(reaction.emoji) in reactions

                                reaction, user = await self.bot.wait_for('reaction_add', check=check)
                                if str(reaction.emoji) == one:
                                    item = 0
                                if str(reaction.emoji) == two:
                                    item = 1
                                if str(reaction.emoji) == three:
                                    item = 2
                                if str(reaction.emoji) == four:
                                    item = 3
                                if str(reaction.emoji) == five:
                                    item = 4
                                if str(reaction.emoji) == six:
                                    item = 5
                                if str(reaction.emoji) == seven:
                                    item = 6
                                if str(reaction.emoji) == eight:
                                    item = 7
                                if str(reaction.emoji) == nine:
                                    item = 8
                                if str(reaction.emoji) == ten:
                                    item = 9
                                if str(reaction.emoji) == ex:
                                    item = 10
                            else:
                                item = 0
                            if not item == 10:
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    titles, specs, images = await asyncio.get_event_loop().run_in_executor(pool, get_specs,
                                                                                                   f"https://pcpartpicker.com{producturls[item]}",
                                                                                                   'noncustom')
                                description = ''
                                if len(specs) > len(titles):
                                    for i in range(0, len(titles)):
                                        if description == '':
                                            description = f'**{titles[i]}:**{specs[i]}'
                                        else:
                                            description = f'{description}\n**{titles[i]}:**{specs[i]}'
                                else:
                                    for i in range(0, len(specs)):
                                        if description == '':
                                            description = f'**{titles[i]}:**{specs[i]}'
                                        else:
                                            description = f'{description}\n**{titles[i]}:**{specs[i]}'
                                embed_msg = discord.Embed(title=productnames[item], description=description, colour=red,
                                                          url=f"https://pcpartpicker.com{producturls[item]}",
                                                          timestamp=datetime.utcnow())

                                if len(images) > 0:
                                    embed_msg.set_thumbnail(url=f"https:{images[0]}")

                                await message.edit(embed=embed_msg)

                            else:
                                embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                                          timestamp=datetime.utcnow())
                                embed_msg.set_footer(text='Powered by PCPartPicker')
                                await message.edit(embed=embed_msg)
                        else:
                            embed_msg = discord.Embed(title=f"No results found for '{search_term}'.", colour=red,
                                                      timestamp=datetime.utcnow())
                            await message.edit(embed=embed_msg)
                    else:
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            titles, specs, images = await asyncio.get_event_loop().run_in_executor(pool, get_specs,
                                                                                           f"https://pcpartpicker.com/search/?q={search_term}",
                                                                                           'noncustom')
                        if not str(titles) == 'rate_limited':
                            description = ''
                            if len(specs) > len(titles):
                                for i in range(0, len(titles)):
                                    if description == '':
                                        description = f'**{titles[i]}:**{specs[i]}'
                                    else:
                                        description = f'{description}\n**{titles[i]}:**{specs[i]}'
                            else:
                                for i in range(0, len(specs)):
                                    if description == '':
                                        description = f'**{titles[i]}:**{specs[i]}'
                                    else:
                                        description = f'{description}\n**{titles[i]}:** {specs[i]}'
                            embed_msg = discord.Embed(title=producturls, description=description, colour=red,
                                                      url=(f"https://pcpartpicker.com/search/?q={search_term}").replace(' ',
                                                                                                                        '%20'),
                                                      timestamp=datetime.utcnow())

                            if len(images) > 0:
                                embed_msg.set_thumbnail(url=f"https:{images[0]}")

                            await message.edit(embed=embed_msg)

                        else:
                            db = open("scrapedata.txt", "w")
                            db.write("0")
                            rate_limited = "0"
                            embed_msg = discord.Embed(
                                title="Sorry, it seems like I am being rate limited. Please try again later.",
                                colour=red, timestamp=datetime.utcnow())
                            await message.edit(content="", embed=embed_msg)
                            quake = self.bot.get_user(405798011172814868)
                            await quake.send(f"Captcha Needed, bot down. Search query: `{search_term}`.")
                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=red, timestamp=datetime.utcnow())
                    await message.edit(content="", embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Search query: `{search_term}`.")
            else:
                embed_msg = discord.Embed(title=f"No results found for '{search_term}'.", colour=red,
                                          timestamp=datetime.utcnow())
                await message.edit(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command(aliases=['pp', 'p', 'price'], description='shows the cheapest price for a part via search query (if the part is available). put the country\'s alpha-2 code (e.g. uk, fr, es) if you wish to see pricing in other regions. only works for supported countries on pcpartpicker. use ,regions to see a full list of supported regions as well as their alpha-2 codes.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partprice(self, ctx, region, *, search_term=None):
        countries = ['ae', 'tr', 'th', 'se', 'es', 'kr', 'sg', 'sa', 'qa', 'pt', 'pl', 'ph', 'om', 'no', 'nl', 'mx',
                     'kw',
                     'jp', 'it', 'il', 'ie', 'in', 'hk', 'de', 'fr', 'fi', 'dk', 'ca', 'br', 'be', 'bh', 'ar', 'us',
                     'uk',
                     'fr', 'nz', 'au']
        await log(self.bot, 'partprice', ctx)
        global rate_limited
        if not region.lower() in countries:
            if search_term == None:
                searchterm = region
            else:
                searchterm = f"{region} {search_term}"
            country = ''
        else:
            searchterm = search_term
            country = f"{region.lower()}."

        if rate_limited == '1':
            embed_msg = discord.Embed(title=f"Finding pricing for '{searchterm}' on PCPartPicker...",
                                      timestamp=datetime.utcnow(), colour=red)
            message = await ctx.send(embed=embed_msg)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, searchterm)
            if not productnames is None:
                if not productnames == 'rate_limited':
                    if not productnames == 'use_current':
                        if not len(productnames) == 0:
                            if not len(productnames) == 1:
                                description = ''
                                for i in range(0, len(productnames)):
                                    if description == '':
                                        description = f"{i + 1}. [{productnames[i]}]({'https://pcpartpicker.com' + producturls[i]})"
                                    else:
                                        description = f"{description}\n{i + 1}. [{productnames[i]}]({'https://pcpartpicker.com' + producturls[i]})"
                                embed_msg = discord.Embed(title=f"Showing results for {searchterm}:",
                                                          description=description, colour=red,
                                                          timestamp=datetime.utcnow())
                                await message.edit(embed=embed_msg)
                                one = "1\N{variation selector-16}\N{combining enclosing keycap}"
                                two = "2\N{variation selector-16}\N{combining enclosing keycap}"
                                three = "3\N{variation selector-16}\N{combining enclosing keycap}"
                                four = "4\N{variation selector-16}\N{combining enclosing keycap}"
                                five = "5\N{variation selector-16}\N{combining enclosing keycap}"
                                six = "6\N{variation selector-16}\N{combining enclosing keycap}"
                                seven = "7\N{variation selector-16}\N{combining enclosing keycap}"
                                eight = "8\N{variation selector-16}\N{combining enclosing keycap}"
                                nine = "9\N{variation selector-16}\N{combining enclosing keycap}"
                                ten = "\N{keycap ten}"
                                ex = "\u274C"
                                reactions = []
                                iterate = 0
                                for r in (one, two, three, four, five, six, seven, eight, nine, ten):
                                    iterate = iterate + 1
                                    if not iterate > len(producturls):
                                        await message.add_reaction(r)
                                        reactions.append(r)
                                await message.add_reaction(ex)
                                reactions.append(ex)

                                def check(reaction, user):
                                    return user == ctx.message.author and str(reaction.emoji) in reactions

                                reaction, user = await self.bot.wait_for('reaction_add', check=check)
                                if str(reaction.emoji) == one:
                                    item = 0
                                if str(reaction.emoji) == two:
                                    item = 1
                                if str(reaction.emoji) == three:
                                    item = 2
                                if str(reaction.emoji) == four:
                                    item = 3
                                if str(reaction.emoji) == five:
                                    item = 4
                                if str(reaction.emoji) == six:
                                    item = 5
                                if str(reaction.emoji) == seven:
                                    item = 6
                                if str(reaction.emoji) == eight:
                                    item = 7
                                if str(reaction.emoji) == nine:
                                    item = 8
                                if str(reaction.emoji) == ten:
                                    item = 9
                                if str(reaction.emoji) == ex:
                                    item = 10
                            else:
                                item = 0
                            if not item == 10:
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    prices, links, sellers, images, stock = await asyncio.get_event_loop().run_in_executor(pool,
                                                                                                            get_price,
                                                                                                            f"https://{country}pcpartpicker.com{producturls[item]}")
                                if not str(prices) == 'rate_limited':
                                    if len(prices) > 0:
                                        try:
                                            cheapestindex = stock.index('In stock')
                                        except ValueError:
                                            cheapestindex = -1
                                        formatted_prices = '\n'.join([f"**[{sellers[i]}]({links[i]}): {prices[i]}**" if i == cheapestindex else f"[{sellers[i]}]({links[i]}): {prices[i]}" for i in range(len(prices))])
                                        embed_msg = discord.Embed(title=f"Pricing for '{productnames[item]}':",
                                                                  description=formatted_prices, colour=red,
                                                                  url=f"https://{country}pcpartpicker.com{producturls[item]}",
                                                                  timestamp=datetime.utcnow())
                                        if len(images) > 0:
                                            embed_msg.set_thumbnail(url=f"https:{images[0]}")

                                        await message.edit(embed=embed_msg)
                                    else:
                                        embed_msg = discord.Embed(
                                            title=f"No pricing available for '{productnames[item]}'.",
                                            description='',
                                            colour=red, timestamp=datetime.utcnow())
                                        embed_msg.set_footer(text='Powered by PCPartPicker')
                                        await message.edit(embed=embed_msg)
                                else:
                                    db = open("scrapedata.txt", "w")
                                    db.write("0")
                                    rate_limited = "0"
                                    embed_msg = discord.Embed(
                                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                                        colour=red, timestamp=datetime.utcnow())
                                    await message.edit(content="", embed=embed_msg)
                                    quake = bot.get_user(405798011172814868)
                                    await quake.send(f"Captcha Needed, bot down. Search query: `{searchterm}`.")
                            else:
                                embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                                          timestamp=datetime.utcnow())
                                embed_msg.set_footer(text='Powered by PCPartPicker')
                                await message.edit(embed=embed_msg)
                        else:
                            embed_msg = discord.Embed(title=f"No results found for '{searchterm}'.", colour=red,
                                                      timestamp=datetime.utcnow())
                            await message.edit(embed=embed_msg)
                    else:
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            prices, links, sellers, images, stock = await asyncio.get_event_loop().run_in_executor(pool, get_price,
                                                                                                    f"https://{country}pcpartpicker.com/search/?q={searchterm}")
                        if not str(prices) == 'rate_limited':
                            if len(prices) > 0:
                                try:
                                    cheapestindex = stock.index('In stock')
                                except ValueError:
                                    cheapestindex = -1
                                formatted_prices = '\n'.join([f"**[{sellers[i]}]({links[i]}): {prices[i]}**" if i == cheapestindex else f"[{sellers[i]}]({links[i]}): {prices[i]}" for i in range(len(prices))])
                                if country == '':
                                    embed_msg = discord.Embed(title=f"Pricing for '{producturls}':",
                                                              description=formatted_prices, colour=red,
                                                              url=f"https://{country}pcpartpicker.com/search/?q={searchterm}".replace(
                                                                  ' ', '%20'),
                                                              timestamp=datetime.utcnow())

                                    if len(images) > 0:
                                        embed_msg.set_thumbnail(url=f"https:{images[0]}")

                                    await message.edit(embed=embed_msg)
                                else:
                                    embed_msg = discord.Embed(
                                        title=f"Pricing for '{producturls}' in {country.upper().replace('.', '')}:",
                                        description=formatted_prices, colour=red,
                                        url=f"https://{country}pcpartpicker.com/search/?q={searchterm}".replace(
                                                                  ' ', '%20'),
                                        timestamp=datetime.utcnow())

                                    if len(images) > 0:
                                        embed_msg.set_thumbnail(url=f"https:{images[0]}")

                                    await message.edit(embed=embed_msg)
                            else:
                                if country == '':
                                    embed_msg = discord.Embed(
                                        title=f"No pricing available for '{producturls}' in the US.",
                                        description='',
                                        colour=red, timestamp=datetime.utcnow())
                                    embed_msg.set_footer(text='Powered by PCPartPicker')
                                    await message.edit(embed=embed_msg)
                                else:
                                    embed_msg = discord.Embed(
                                        title=f"No pricing available for '{producturls}' in {country.upper()}.",
                                        description='',
                                        colour=red, timestamp=datetime.utcnow())
                                    embed_msg.set_footer(text='Powered by PCPartPicker')
                                    await message.edit(embed=embed_msg)
                        else:
                            db = open("scrapedata.txt", "w")
                            db.write("0")
                            rate_limited = "0"
                            embed_msg = discord.Embed(
                                title="Sorry, it seems like I am being rate limited. Please try again later.",
                                colour=red, timestamp=datetime.utcnow())
                            await message.edit(content="", embed=embed_msg)
                            quake = self.bot.get_user(405798011172814868)
                            await quake.send(f"Captcha Needed, bot down. Search query: `{searchterm}`.")
                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=red, timestamp=datetime.utcnow())
                    await message.edit(content="", embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Search query: `{query}`.")
            else:
                embed_msg = discord.Embed(title=f"No results found for '{searchterm}'.", colour=red,
                                          timestamp=datetime.utcnow())
                await message.edit(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command(aliases=['psc', 'specscustom', 'sc'], description='shows detailed specs for a part via pcpartpicker link.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partspecscustom(self, ctx, url):
        await log(self.bot, 'partspecscustom', ctx)
        global rate_limited
        if rate_limited == "1":
            embed_msg = discord.Embed(title="Finding specs...", timestamp=datetime.utcnow(), colour=red)
            message = await ctx.send(embed=embed_msg)
            try:
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    titles, specs, name, images = await asyncio.get_event_loop().run_in_executor(pool, get_specs, url, 'custom')
                if not str(titles) == 'rate_limited':
                    description = ''
                    if len(specs) > len(titles):
                        for i in range(0, len(titles)):
                            if description == '':
                                description = f'**{titles[i]}:** {specs[i]}'
                            else:
                                description = f'{description}\n**{titles[i]}:** {specs[i]}'
                    else:
                        for i in range(0, len(specs)):
                            if description == '':
                                description = f'**{titles[i]}:** {specs[i]}'
                            else:
                                description = f'{description}\n**{titles[i]}:** {specs[i]}'
                    embed_msg = discord.Embed(title=name, description=description, colour=red,
                                              url=url,
                                              timestamp=datetime.utcnow())

                    if len(images) > 0:
                        embed_msg.set_thumbnail(url=f"https:{images[0]}")


                    await message.edit(embed=embed_msg)
                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=red, timestamp=datetime.utcnow())
                    await message.edit(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: partspecscustom")
            except requests.exceptions.MissingSchema:
                embed_msg = discord.Embed(title=f"No results found for {url}.", colour=red, timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by PCPartPicker')
                await message.edit(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        global rate_limited
        try:
            if not message.guild.id == 246414844851519490:
                if rate_limited == '1':
                    if not message.author.id == 769886576321888256:
                        if 'https://' and 'pcpartpicker' in message.content:
                            if not ',updatebuild' in message.content and not ',createbuild' in message.content:
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
                                found_url = False
                                positions = []
                                ctxurls = []
                                for i in urls:
                                    if i in message.content:
                                        matches = re.finditer(i, message.content)
                                        matches_positions = [match.start() for match in matches]
                                    for i in matches_positions:
                                        positions.append(i)
                                    matches_positions = []
                                if len(positions) > 0:
                                    for i in positions:
                                        counter = i
                                        while not f"{message.content[counter]}{message.content[counter + 1]}{message.content[counter + 2]}{message.content[counter + 3]}{message.content[counter + 4]}" == "list/":
                                            counter = counter + 1
                                        ctxurls.append(
                                            message.content[positions[positions.index(i)]:(counter + 11)].replace(' ', ''))
                                if len(ctxurls) > 0:
                                    for i in ctxurls:
                                        theurl = i
                                        with concurrent.futures.ThreadPoolExecutor() as pool:
                                            embed_msg, thelist, pricing_breakdown_embed = await asyncio.get_event_loop().run_in_executor(pool, format_link, i, message)
                                            if not thelist == 'rate_limited':

                                                issues = []

                                                if 'H510' in thelist or 'H710' in thelist or 'S340' in thelist:
                                                    issues.append('NZXT cases have limited airflow. Using these cases may result in increased noise and overheating components.')
                                                if 'QVO' in thelist and 'Samsung' in thelist:
                                                    issues.append('The Samsung QVO line of SSDs use QLC NAND flash which makes the SSD slow down as it fills up as well as make the SSD have a decreased linespan.')
                                                if 'Thermaltake Smart' in thelist:
                                                    issues.append('Thermaltake Smart is a notoriously bad PSU with lacking protections.')
                                                if 'S12II' in thelist:
                                                    issues.append('The Seasonic S12II/III are bad power supplies which lack OTP as well as have sleeve bearing fans.')
                                                if 'System Power 9' in thelist:
                                                    issues.append('The be quiet! System Power 9 has a sleeve bearing fan which hinders its reliability and lifespan. It also doesn\'t have very well configured OTP.')
                                                if 'Western Digital Blue' in thelist:
                                                    issues.append('WD Blue has unknown ECC/wear levelling. Nobody can tell if its good or bad.')
                                                if 'Hyper 212' in thelist:
                                                    issues.append('The Hyper 212 EVO has a sleeve bearing fan which hinders its reliability and lifespan. The other Hyper 212\'s have mediocre bearings too.')
                                                if 'MF120' in thelist:
                                                    issues.append('The CoolerMaster MF120 fans have bad noise normalized performance as well as mediocre fan bearings.')
                                                if 'LL120' in thelist or 'LL140' in thelist:
                                                    issues.append('The Corsair LL120/LL140 fans have bad noise normalized performance as well as mediocre fan bearings.')
                                                if 'B450M PRO4' in thelist or 'B450 Pro4' in thelist:
                                                    issues.append('The B450(M) PRO4 has no Load Line Calibration meaning increased voltage droop.')
                                                if 'Western Digital Green' in thelist:
                                                    issues.append('WD Green is a DRAMless SSD meaning it can be slower than a hard drive.')
                                                if 'Kingston A400' in thelist:
                                                    issues.append('Kingston A400 is a DRAMless SSD meaning it can be slower than a hard drive.')
                                                if 'Crucial BX500' in thelist:
                                                    issues.append('The Crucial BX500 is a DRAMless SSD meaning it can be slower than a hard drive.')
                                                if 'TCSunBow X3' in thelist:
                                                    issues.append('The TCSunBow X3 has a DRAM lottery meaning some have DRAM and some don\'t. The DRAMless version can be slower than a hard drive.')
                                                if '1660 Ti' in thelist:
                                                    issues.append('The GTX 1660 Ti is usually not worth it if the GTX 1660 SUPER is cheaper or the RX 5600 XT is the same price.')
                                                if 'SPEC-DELTA' in thelist:
                                                    issues.append('Corsair SPEC-DELTA has bad airflow meaning that using it may result in increased noise and overheating components.')
                                                if '220T' in thelist:
                                                    issues.append('The Corsair 220T series of cases (including the airflow version) has poor airflow. Using them may result in increased noise and overheating components.')
                                                if '275R' in thelist:
                                                    issues.append('The Corsair 275R series of cases (including the airflow version) has poor airflow. Using them may result in increased noise and overheating components.')
                                                if 'A320' in thelist:
                                                    issues.append('Using A320 or A520 motherboards are usually not worth it because of their tendencies to have weak VRMs as well as other disadvantages like no overclocking.')
                                                if 'VS450' in thelist or 'VS550' in thelist or 'CV450' in thelist or 'CV550' in thelist:
                                                    issues.append('Corsair VS/CV power supplies are lacking protections and have poor fans.')
                                                if 'EVGA BR' in thelist or 'EVGA BA' in thelist or 'EVGA BQ' in thelist:
                                                    issues.append('EVGA BR/BA/BQ power supplies are lacking protections and have ripple issues.')
                                                if 'WINDFORCE' in thelist:
                                                    issues.append('Gigabyte WINDFORCE graphics cards have sleeve bearing fans which hinder their reliability and lifespan.')
                                                if 'Thermaltake' in thelist and 'UX100' in thelist:
                                                    issues.append('The Thermaltake UX100 is a poor performing CPU cooler.')
                                                if 'B450M DS3H' in thelist or 'B450M S2H' in thelist:
                                                    issues.append('The B450M DS3H and S2H have weak VRMs meaning that you may have issues with future upgrades.')
                                                if 'MasterLiquid' in thelist:
                                                    issues.append('CM MasterLiquid AIOs have worse performance than similarly priced air coolers and they have leaking issues.')
                                                if 'Asus PRIME B450' in thelist:
                                                    issues.append('Asus PRIME B450 motherboards have weak VRMs.')
                                                if '60 GB' in thelist or '120 GB' in thelist or '60GB' in thelist or '120GB' in thelist or '250 GB' in thelist or '250GB' in thelist or '256GB' in thelist or '256 GB' in thelist or '128GB' in thelist or '128 GB' in thelist:
                                                    issues.append('Low capacity storage mediums are usually not worth it because of their poor value.')
                                                if 'Power Supply' in thelist and not '80+' in thelist:
                                                    issues.append('Unrrated Power Supplies are usually poor performing/have other issues.')

                                                if '1 x 16 GB' in thelist:
                                                    issues.append('Single channel memory has less bandwidth than dual channel which calls for a significant performance loss.')
                                                if '1 x 8 GB' in thelist:
                                                    issues.append('Single channel memory has less bandwidth than dual channel which calls for a significant performance loss.')
                                                if 'CXM' in thelist:
                                                    issues.append('CXM uses double forward as a primary topology which is an inefficient design and is likely to whine due to the use of hard switching.')
                                                if not 'Solid State Drive' in thelist:
                                                    issues.append('Your list doesn\'t have a Solid State Drive. Having one will speed up your loading times significantly.')

                                                formattedmessage = await message.channel.send(embed=embed_msg)
                                                #formattedmessage2 = await message.channel.send(embed=pricing_breakdown_embed)

                                                description = ''

                                                for i in range(len(issues)):
                                                    description = f"{description}\n**{i+1}.** {issues[i]}"

                                                if not len(issues) == 0:
                                                    await formattedmessage.add_reaction("⚠")
                                                    embed_msg = discord.Embed(title=f"Found {len(issues)} potential issue(s) with your list", description=description, timestamp=datetime.utcnow(), colour=red, url=theurl)

                                                    warning = ['⚠']

                                                    def check(reaction, user):
                                                        return user == message.author and str(reaction.emoji) in warning

                                                    reaction, user = await self.bot.wait_for('reaction_add', check=check)

                                                    await message.author.send(embed=embed_msg)

        except:
            pass
    @commands.command()
    async def regions(self, ctx):
        codes = ['ae', 'tr', 'th', 'se', 'es', 'kr', 'sg', 'sa', 'qa', 'pt', 'pl', 'ph', 'om', 'no', 'nl', 'mx',
                       'kw',
                       'jp', 'it', 'il', 'ie', 'in', 'hk', 'de', 'fr', 'fi', 'dk', 'ca', 'br', 'be', 'bh', 'ar', 'us',
                       'uk',
                       'fr', 'nz', 'au']
        countries = ['United Arab Emirates', 'Turkey', 'Thailand', 'Sweden', 'Spain', 'South Korea', 'Singapore',
                           'Saudi Arabia', 'Qatar', 'Portugal', 'Poland', 'Philippines', 'Oman', 'Norway', 'Netherlands',
                           'Mexico', 'Kuwait', 'Japan', 'Italy',
                           'Israel', 'Ireland', 'India', 'Hong Kong', 'Germany', 'France', 'Finland', 'Denmark',
                           'Canada', 'Brazil', 'Belgium', 'Bahrain', 'Argentina', 'United States', 'United Kingdom',
                           'France', 'New Zealand', 'Australia']

        description = ''
        for i in range(0, len(codes) - 1):
            if description == '':
                description = f"**{codes[i]}**: {countries[i]}"
            else:
                description = f"{description}\n**{codes[i]}**: {countries[i]}"
        embed_msg = discord.Embed(title="Supported Regions", description=description,
                                  colour=red, timestamp=datetime.utcnow())
        await ctx.message.author.send(embed=embed_msg)
        await ctx.message.add_reaction('📨')

    @commands.command(aliases=['guides', 'buildguide'], description='retrieves the pcpartpicker build guides and allows you to choose a guide for viewing. if no region code is put, the command will default to US.')
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def buildguides(self, ctx, country=None):

        global rate_limited

        if rate_limited == "1":

            codes = ['ae', 'tr', 'th', 'se', 'es', 'kr', 'sg', 'sa', 'qa', 'pt', 'pl', 'ph', 'om', 'no', 'nl', 'mx',
                     'kw',
                     'jp', 'it', 'il', 'ie', 'in', 'hk', 'de', 'fr', 'fi', 'dk', 'ca', 'br', 'be', 'bh', 'ar', 'us',
                     'uk',
                     'fr', 'nz', 'au']

            worked = True

            if country is None:
                url = 'https://pcpartpicker.com/guide/'
                country = ''

            elif country in codes:
                url = f'https://{country}.pcpartpicker.com/guide/'
                country = f"{country}."

            elif country.lower() in codes:
                url = f'https://{country.lower()}.pcpartpicker.com/guide/'
                country = f"{country.lower()}."

            else:
                embed_msg = discord.Embed(title=f"'{country}' is not a valid region!",
                                          description="Use `,regions` for a list of supported regions.\nIf no region is given, the command will default to the US.",
                                          colour=red, timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
                worked = False

            if worked is True:
                embed_msg = discord.Embed(title=f"Fetching guides...",
                                          colour=red, timestamp=datetime.utcnow())
                send = await ctx.send(embed=embed_msg)
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    names, prices, urls = await asyncio.get_event_loop().run_in_executor(pool, get_build_guides, url)

                if not type(names) is str:
                    description = ''

                    for i in range(0, len(names)):
                        if description == '':
                            description = f"{i + 1}. [{names[i]} ({prices[i]})]({f'https://{country}pcpartpicker.com{urls[i]}'})"
                        else:
                            description = f"{description}\n{i + 1}. [{names[i]} ({prices[i]})]({f'https://{country}pcpartpicker.com{urls[i]}'})"
                    embed_msg = discord.Embed(title="PCPartPicker Build Guides",
                                              description=description,
                                              colour=red, timestamp=datetime.utcnow(), url=url)
                    embed_msg.add_field(name="Send ' , ' and then the corresponding number of the build in chat.",
                                        value='For example, `,10`.', inline=False)
                    await send.edit(embed=embed_msg)

                    def check(message):
                        return len(message.content) > 0 and message.content[0] == ',' and message.channel == ctx.message.channel

                    message = await self.bot.wait_for('message', check=check)
                    worked = True
                    try:
                        item = int(message.content[1:]) - 1
                    except ValueError:
                        embed_msg = discord.Embed(title=f"'{message.content[1:]}' is not a number!", colour=red,
                                                  timestamp=datetime.utcnow())
                        await send.edit(embed=embed_msg)
                        worked = False
                    if worked is True:

                        embed_msg = discord.Embed(title=f"Fetching build...",
                                                  colour=red, timestamp=datetime.utcnow())
                        await send.edit(embed=embed_msg)

                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            productnames, producttypes, prices, images, wattage = await asyncio.get_event_loop().run_in_executor(
                                pool, get_build, f'https://{country}pcpartpicker.com{urls[item]}')

                            if not wattage == 'rate_limited':

                                description = ''

                                for i in range(len(productnames)):
                                    if description == '':
                                        description = f"**{producttypes[i]}:** {productnames[i]}"
                                    else:
                                        description = f"{description}\n**{producttypes[i]}:** {productnames[i]}"
                                embed_msg = discord.Embed(title=names[item],
                                                          description=f"{description}\n\n**Estimated Wattage:** {wattage}\n**Total:** {prices[-1]}",
                                                          colour=red, timestamp=datetime.utcnow(),
                                                          url=f'https://{country}pcpartpicker.com{urls[item]}')
                                if len(images) > 0:
                                    embed_msg.set_thumbnail(url=f"https:{images[0]}")
                                await send.edit(embed=embed_msg)

                            else:
                                db = open("scrapedata.txt", "w")
                                db.write("0")
                                rate_limited = "0"
                                embed_msg = discord.Embed(
                                    title="Sorry, it seems like I am being rate limited. Please try again later.",
                                    colour=red, timestamp=datetime.utcnow())
                                await send.edit(content="", embed=embed_msg)
                                quake = self.bot.get_user(405798011172814868)
                                await quake.send(f"Captcha Needed, bot down. Command: buildguides.")
                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=red, timestamp=datetime.utcnow())
                    await ctx.send(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: buildguides.")

        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def trends(self, ctx, *, part='cpu'):

        global rate_limited

        if rate_limited == "1":
            parts = ['cpu', 'memory', 'monitor', 'power supply', 'storage', 'video card']

            if part.lower() in parts:

                url = f"https://pcpartpicker.com/trends/price/{part.replace(' ', '-')}/"

                page = requests.get(url)
                soup = BeautifulSoup(page.content, 'html.parser')

                images = []
                titles = []

                realtext = ''

                for a in soup.find_all(class_='pageTitle'):
                    realtext = a.get_text()

                if not realtext == 'Verification':

                    for img in soup.find_all('img', src=True):
                        if img['src'].startswith('//cdna.pcpartpicker.com/static/forever/images/trends/'):
                            images.append(img['src'])

                    for title in soup.find_all(class_='block'):
                        titles.append(title.get_text().replace(
                            '\n\nJump Menu\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nJump to price trends for:\n\n\n\n\n',
                            ''))

                    titles_list = titles[0].split('\n')

                    embeds = []

                    for i in range(len(images)):
                        embeds.append(discord.Embed(title=f"Price trends for '{part}':", description=titles_list[i], colour=red,
                                                    timestamp=datetime.utcnow()).set_image(url=f"https:{images[i]}").set_footer(
                            text=f'Page {i + 1} out of {len(images)}'))

                    paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout=30)
                    paginator.add_reaction('⏪', "back")
                    paginator.add_reaction('⏩', "next")
                    paginator.add_reaction('❌', "lock")

                    await paginator.run(embeds)

                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=red, timestamp=datetime.utcnow())
                    await ctx.send(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: trends")

            else:
                parts_list = "".join([f"- `{s}`\n" for s in parts])
                embed_msg = discord.Embed(title=f"'{part}' is not a supported part!",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.add_field(name='Supported Parts:', value=parts_list, inline=False)
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)


    @commands.command(aliases=['pcforums', 'pcppforum', 'pcforum', 'pcpartpickerforum', 'pcpartpickerforums'],
                 description='browses the pcpartpicker forums. if no valid forum name or index is given, all forums are sent and decided on.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def pcppforums(self, ctx, *, forum=None):

        global rate_limited

        if rate_limited == '1':

            with concurrent.futures.ThreadPoolExecutor() as pool:
                incompletelinks, titles = await asyncio.get_event_loop().run_in_executor(pool, get_pcpp_subforums)

            if not str(incompletelinks) == 'rate_limited':
                links = [f"https://pcpartpicker.com{link}" for link in incompletelinks]
                attempt = 'attempted'
                if forum is None:
                    description = ''
                    cycles = -1
                    times = math.ceil(len(titles) / 2)
                    for i in range(0, times):
                        if description == '':
                            description = f"{i + 1}. [{titles[i]}]({links[i]})"
                        else:
                            description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                        cycles = cycles + 1
                    embed_msg = discord.Embed(title="Select Subforum:", description=description, colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                    await ctx.send(embed=embed_msg)
                    todo = len(titles) - cycles
                    description = ''
                    for i in range(todo, len(titles)):
                        if description == '':
                            description = f"{i + 1}. [{titles[i]}]({links[i]})"
                        else:
                            description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                    embed_msg = discord.Embed(title="", description=description, colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                    await ctx.send(embed=embed_msg)
                    embed_msg = discord.Embed(title="",
                                              colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.add_field(name="Send ' , ' and then the corresponding number of the subforum in chat.",
                                        value="E.g, `,10`.")
                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                    await ctx.send(embed=embed_msg)

                    def check(message):
                        return len(message.content) > 0 and message.content[
                            0] == ',' and message.channel == ctx.message.channel

                    message = await self.bot.wait_for('message', check=check)
                    try:
                        item = int(message.content[1:]) - 1
                    except ValueError:
                        embed_msg = discord.Embed(title=f"'{message.content[1:]}' is not a number!", colour=red,
                                                  timestamp=datetime.utcnow())
                        embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                        await ctx.send(embed=embed_msg)
                else:
                    try:
                        item = int(forum) - 1
                    except:
                        lowertitles = []
                        for i in titles:
                            lowertitles.append(i.lower())
                        try:
                            item = lowertitles.index(forum)
                        except:
                            embed_msg = discord.Embed(
                                title=f"No forum found with index or name '{forum}'. Use `,pcppforums` for a full list of forums.",
                                colour=red,
                                timestamp=datetime.utcnow())
                            embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            await ctx.send(embed=embed_msg)
                            attempt = 'failed'
                if not attempt == 'failed':
                    try:
                        titlesog = titles
                        link_used = links[item]
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            incompletelinks, titles = await asyncio.get_event_loop().run_in_executor(pool, get_pcpp_posts,
                                                                                                     links[item])
                        if not str(incompletelinks) == 'rate_limited':
                            links = [f"https://pcpartpicker.com{link}" for link in incompletelinks]
                            description = ''
                            if len(titles) > 10:
                                for i in range(10):
                                    if description == '':
                                        description = f"{i + 1}. [{titles[i]}]({links[i]})"
                                    else:
                                        description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                                embed_msg = discord.Embed(title=f"Posts in {titlesog[item]}:", description=description,
                                                          colour=red,
                                                          timestamp=datetime.utcnow(), url=link_used)
                                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            else:
                                for i in range(len(titles)):
                                    if description == '':
                                        description = f"{i + 1}. [{titles[i]}]({links[i]})"
                                    else:
                                        description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                                embed_msg = discord.Embed(title=f"Posts in {titlesog[item]}:", description=description,
                                                          colour=red,
                                                          timestamp=datetime.utcnow(), url=link_used)
                                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            message = await ctx.send(embed=embed_msg)
                            one = "1\N{variation selector-16}\N{combining enclosing keycap}"
                            two = "2\N{variation selector-16}\N{combining enclosing keycap}"
                            three = "3\N{variation selector-16}\N{combining enclosing keycap}"
                            four = "4\N{variation selector-16}\N{combining enclosing keycap}"
                            five = "5\N{variation selector-16}\N{combining enclosing keycap}"
                            six = "6\N{variation selector-16}\N{combining enclosing keycap}"
                            seven = "7\N{variation selector-16}\N{combining enclosing keycap}"
                            eight = "8\N{variation selector-16}\N{combining enclosing keycap}"
                            nine = "9\N{variation selector-16}\N{combining enclosing keycap}"
                            ten = "\N{keycap ten}"
                            ex = "\u274C"
                            reactions = []
                            iterate = 0
                            for r in (one, two, three, four, five, six, seven, eight, nine, ten):
                                iterate = iterate + 1
                                if not iterate > len(titles):
                                    await message.add_reaction(r)
                                    reactions.append(r)
                            await message.add_reaction(ex)
                            reactions.append(ex)

                            def check(reaction, user):
                                return user == ctx.message.author and str(reaction.emoji) in reactions

                            reaction, user = await self.bot.wait_for('reaction_add', check=check)
                            if str(reaction.emoji) == one:
                                item = 0
                            if str(reaction.emoji) == two:
                                item = 1
                            if str(reaction.emoji) == three:
                                item = 2
                            if str(reaction.emoji) == four:
                                item = 3
                            if str(reaction.emoji) == five:
                                item = 4
                            if str(reaction.emoji) == six:
                                item = 5
                            if str(reaction.emoji) == seven:
                                item = 6
                            if str(reaction.emoji) == eight:
                                item = 7
                            if str(reaction.emoji) == nine:
                                item = 8
                            if str(reaction.emoji) == ten:
                                item = 9
                            if str(reaction.emoji) == ex:
                                item = 10
                            if not item == 10:
                                embed_msg = discord.Embed(title="Fetching post...",
                                                          description=f"Depending on the length of the post, this could take a while.",
                                                          colour=red,
                                                          timestamp=datetime.utcnow(), url=links[item])
                                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                                await message.edit(embed=embed_msg)
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    content, details = await asyncio.get_event_loop().run_in_executor(pool, get_pcpp_post,
                                                                                                      links[item])

                                if not str(content) == 'rate_limited':

                                    contenttodisplay = content[0]
                                    if len(contenttodisplay) > 2040:
                                        contenttodisplay = f"{contenttodisplay[0:2040]}..."
                                    embed_msg = discord.Embed(title=titles[item], description=f"{contenttodisplay}",
                                                              colour=red,
                                                              timestamp=datetime.utcnow(), url=links[item])
                                    embed_msg.add_field(name='Extra Details',
                                                        value="Posted by " + details[0].replace('\n', '') + ".",
                                                        inline=False)
                                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                                    await message.edit(embed=embed_msg)
                                else:
                                    db = open("scrapedata.txt", "w")
                                    db.write("0")
                                    rate_limited = "0"
                                    embed_msg = discord.Embed(
                                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                                        colour=red, timestamp=datetime.utcnow())
                                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                                    await ctx.send(embed=embed_msg)
                                    quake = self.bot.get_user(405798011172814868)
                                    await quake.send(f"Captcha Needed, bot down. Command: pcppforums")
                            else:
                                embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                                          timestamp=datetime.utcnow())
                                embed_msg.set_footer(name='Powered by pcpartpicker.com/forums')
                                await message.edit(embed=embed_msg)

                        else:
                            db = open("scrapedata.txt", "w")
                            db.write("0")
                            rate_limited = "0"
                            embed_msg = discord.Embed(
                                title="Sorry, it seems like I am being rate limited. Please try again later.",
                                colour=red, timestamp=datetime.utcnow())
                            embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            await ctx.send(embed=embed_msg)
                            quake = self.bot.get_user(405798011172814868)
                            await quake.send(f"Captcha Needed, bot down. Command: pcppforums")

                    except ValueError:
                        embed_msg = discord.Embed(title=f"'{item}' is an invalid number!", colour=red,
                                                  timestamp=datetime.utcnow())
                        embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                        await ctx.send(embed=embed_msg)

            else:
                db = open("scrapedata.txt", "w")
                db.write("0")
                rate_limited = "0"
                embed_msg = discord.Embed(
                    title="Sorry, it seems like I am being rate limited. Please try again later.",
                    colour=red, timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                await ctx.send(embed=embed_msg)
                quake = self.bot.get_user(405798011172814868)
                await quake.send(f"Captcha Needed, bot down. Command: pcppforums")

        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=red, timestamp=datetime.utcnow())
            embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
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
    async def cases(self, ctx, *, tier='None'):

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

        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from cases")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        tiers = ['High End Cases ($$$$)', 'Midrange Cases ($$$)', 'Low End Cases ($$)', 'Budget Cases ($)']

        high_end_cases = ''
        midrange_cases = ''
        low_end_cases = ''
        budget_cases = ''

        if tier == 'None':

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

            descs = [i for i in (high_end_cases, midrange_cases, low_end_cases, budget_cases)]

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

            reaction, user = await self.bot.wait_for('reaction_add', check=check)

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
                cursor = await conn.execute(f"DELETE FROM cases WHERE name = '{case_name}'")
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

    @commands.command()
    async def overview(self, ctx, *, part):
        global rate_limited
        if rate_limited == "1":
            embed_msg = discord.Embed(title=f"Finding info for '{part}' on PCPartPicker...", colour=red, timestamp=datetime.utcnow())
            send = await ctx.send(embed=embed_msg)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, part)
            if productnames == "rate_limited":
                db = open("scrapedata.txt", "w")
                db.write("0")
                rate_limited = "0"
                embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.", colour=red, timestamp=datetime.utcnow())
                await send.edit(embed=embed_msg)
                quake = self.bot.get_user(405798011172814868)
                await quake.send(f"Captcha Needed, bot down. Command: overview, {part}")
                return
            elif len(productnames) == 0:
                embed_msg = discord.Embed(title=f"No results found for '{part}'.", colour=red, timestamp=datetime.utcnow())
                await send.edit(embed=embed_msg)
            elif not productnames == "rate_limited" and len(productnames) > 0:
                description = '\n'.join([f"{i+1}. [{productnames[i]}]({f'https://pcpartpicker.com{producturls[i]}'})" for i in range(len(productnames))])
                embed_msg = discord.Embed(title=f"Showing results for {part}:", description=description, colour=red)
                embed_msg.set_footer(text="Powered by PCPartPicker")
                await send.edit(embed=embed_msg)
                reactions = ["1\N{variation selector-16}\N{combining enclosing keycap}",
                             "2\N{variation selector-16}\N{combining enclosing keycap}",
                             "3\N{variation selector-16}\N{combining enclosing keycap}",
                             "4\N{variation selector-16}\N{combining enclosing keycap}",
                             "5\N{variation selector-16}\N{combining enclosing keycap}",
                             "6\N{variation selector-16}\N{combining enclosing keycap}",
                             "7\N{variation selector-16}\N{combining enclosing keycap}",
                             "8\N{variation selector-16}\N{combining enclosing keycap}",
                             "9\N{variation selector-16}\N{combining enclosing keycap}",
                             "\N{keycap ten}",
                             "\u274C"]

                if len(listofchoices) > 10:
                    listofchoices = listofchoices[:9]

                for i in range(len(listofchoices)):
                    await message.add_reaction(reactions[i])

                await message.add_reaction(reactions[-1])

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in reactions

                reaction, user = await self.bot.wait_for('reaction_add', check=check)

                if not str(reaction.emoji) == reactions[-1]:
                    item = reactions.index(str(reaction.emoji))
                else:
                    embed_msg = discord.Embed(title=f"Operation Cancelled.", colour=red)
                    embed_msg.set_footer(text="Powered by PCPartPicker")
                    return
        else:
            embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.", colour=red, timestamp=datetime.utcnow())
            embed_msg.set_footer(text="Powered by PCPartPicker")
            await ctx.send(embed=embed_msg)

def setup(bot):
    bot.add_cog(PCPartPicker(bot))