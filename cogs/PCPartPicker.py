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
import json
import string

green = discord.Colour(0x1e807c)

allowed_ids = [405798011172814868, 370611001948635157, 287256464047865857, 454186048721780751, 191280151084924928, 698634807143563424, 411274336847134730, 479319375149662209, 750353117698064497, 629736214345416734, 746775313593270352]

def query(search_term):
    page = requests.get(f"https://pcpartpicker.com/search/?q={search_term}")
    soup = BeautifulSoup(page.content, 'html.parser')
    product_name = soup.find(class_='pageTitle').get_text()
    if product_name != 'Product Search': # if the search query redirects straight to a product page
        return 'use_current', 'use_current'
    productnames = []
    producturls = []
    for a in soup.find_all(class_='search_results--link'): # finds the names of the products
        productnames.append(a.get_text().replace('\n', '').replace('\\', '\n'))
    for a in soup.find_all(href=True): # finds the product links
        if not a['href'].startswith('/product/') or a['href'] in producturls: # makes sure its a PCPP product URL and
            continue                                                          # that it's not already in the list
        producturls.append(a['href'])
    return productnames[:10], producturls[:10]



def get_specs(url):
    spec_names = []
    spec_values = []
    images = []

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    product_name = soup.find(class_='pageTitle').get_text()
    for img in soup.find_all('img', src=True):
        if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
            images.append(img['src'])

    for a in soup.find_all(class_='group__title'):
        name = a.get_text().replace('\n', '').replace('\\', '\n')
        if name in spec_names:
            continue
        spec_names.append(name)

    for a in soup.find_all(class_='group__content'):
        text = a.get_text().replace('\n', ' ').replace('\\', '\n')
        spec_values.append(text)

    spec_names = list(dict.fromkeys(spec_names))
    return spec_names, spec_values, images, product_name





def get_price(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    page_title = soup.find(class_='pageTitle').get_text()
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
        sellers.append(a.select('img')[0]['alt']) #.split()[0]
    for img in soup.find_all('img', src=True):
        if '//cdna.pcpartpicker.com/static/forever/images/product/' in img['src']:
            images.append(img['src'])
    links = list(dict.fromkeys(links))
    return prices, links, sellers, images, stock, page_title



def format_pcpp_link(url):
    producturls = []
    productnames = []

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')


    for a in soup.find_all(class_='td__name'):
        if 'From parametric selection:' in a.get_text():
            productnames.append(a.get_text().split('From parametric selection:')[0].replace('\n', ''))
        elif 'From parametric filter:' in a.get_text():
            productnames.append(a.get_text().split('From parametric filter:')[0].replace('\n', ''))
        else:
            productnames.append(a.get_text().replace('\n', ''))
        if 'a href=' in str(a) and not '#view_custom_part' in str(a):
            elements = str(a).split('"')
            for element in elements:
                if element.startswith("/product/"):
                    producturls.append(f"{url.split('com')[0]}com{element}")
        else:
            producturls.append(None)

    producttypes = [a.get_text().replace('\n', '') for a in soup.find_all(class_='td__component')]

    products = []

    for i in range(len(producttypes)):
        products.append((producttypes[i], productnames[i], producturls[i]))

    try:
        wattage = soup.find(class_='partlist__keyMetric').get_text().replace('\n', '').replace("Estimated Wattage:", '')
    except (AttributeError, IndexError):
        wattage = None

    prices = [a.get_text() for a in soup.find_all(class_='td__price')]

    if len(prices) == 0: prices = None

    page_title = soup.find(class_="pageTitle").get_text()

    return products, wattage, prices, page_title


def format_product_link(url):

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    compatible_links = [f"[{a.get_text()}]({url.split('com')[0] + 'com'}{a['href']})" for a in soup.find_all(href=True) if "compatible" in a["href"]]
    product_name = soup.find(class_="pageTitle").get_text()
    prices = [f"{a.get_text()}" for a in soup.find_all(class_="td__finalPrice")]
    buy_links = [f"{url.split('com')[0] + 'com'}{a['href']}" for a in soup.find_all(href=True) if a["href"].startswith("/mr/")]
    vendors = [a.select('img')[0]['alt'] for a in soup.find_all(class_='td__logo')]
    stock = [a.get_text().replace('\n', '') for a in soup.find_all(class_="td__availability td__availability--inStock")]
    try:
        index = stock.index('In stock')
    except ValueError:
        index = None
    images = [a["src"] for a in soup.find_all('img', src=True) if "cdna.pcpartpicker.com/static/forever/images/product/" in a["src"]]
    if len(images) == 0:
        image = None
    else:
        image = f"https:{images[0]}"
    if index != None:
        best_price = (prices[index].replace('\n', ''), f"[{vendors[index]}]({buy_links[index]})")
    else:
        best_price = None

    return product_name, compatible_links, best_price, image

async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title=f"Command '{command}' used by {str(ctx.message.author)}.", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=green, timestamp=datetime.utcnow())
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


# async def update_db()


class PCPartPicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['specs', 'ps', 's'], description='shows detailed specs for a part via search query. if multiple results are returned, user must react with appropriate emoji to get the desired term.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partspecs(self, ctx, *, search_term):
        await log(self.bot, 'partspecs', ctx)
        embed_msg = discord.Embed(title=f"Finding specs for '{search_term}' on PCPartPicker...", timestamp=datetime.utcnow(), colour=green)
        message = await ctx.send(embed=embed_msg)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, search_term)

        if len(productnames) == 0:
            embed_msg = discord.Embed(title=f"No results found for '{search_term}'.", colour=green, timestamp=datetime.utcnow())
            await message.edit(embed=embed_msg)
            return
        elif len(productnames) == 1:
            product_url = f"https://pcpartpicker.com{producturls[0]}"
        elif productnames == 'use_current':
            product_url = f"https://pcpartpicker.com/search/?q={search_term}"
        else:
            slices = [f"{i + 1}. [{productnames[i]}]({f'https://pcpartpicker.com{producturls[i]}'})" for i in range(len(productnames)) if i < 10]
            while True:
                total = sum([len(item) for item in slices])
                if total < 1900:
                    break
                slices.pop(-1)
            description = '\n'.join(slices)
            embed_msg = discord.Embed(title=f"Showing results for {search_term}:", description=description, colour=green, timestamp=datetime.utcnow())
            await message.edit(embed=embed_msg)

            for i in range(len(slices)):
                await message.add_reaction(self.bot.reactions[i])

            await message.add_reaction(self.bot.reactions[-1])

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in self.bot.reactions and reaction.message == message
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                embed_msg = discord.Embed(title="Timed out.", colour=green, timestamp=datetime.utcnow())
                await message.edit(embed=embed_msg)
                try:
                    await message.clear_reactions()
                except:
                    pass
                return
            if not str(reaction.emoji) == self.bot.reactions[-1]:
                product_url = f"https://pcpartpicker.com{producturls[self.bot.reactions.index(str(reaction.emoji))]}"
            else:
                await message.delete()
                return

        with concurrent.futures.ThreadPoolExecutor() as pool:
             spec_titles, spec_values, images, product_name = await asyncio.get_event_loop().run_in_executor(pool, get_specs, product_url)

        description = '\n'.join([f"**{spec_titles[i]}:**{spec_values[i]}" for i in range(len(spec_titles))])
        embed_msg = discord.Embed(title=product_name, description=description, colour=green, url=product_url.replace(' ', '+'), timestamp=datetime.utcnow())
        if len(images) > 0: embed_msg.set_thumbnail(url=f"https:{images[0]}")
        
        await message.edit(embed=embed_msg)
        
        try:
            await message.clear_reactions()
        except:
            pass




    @commands.command(aliases=['pp', 'p', 'price'], description='shows the cheapest price for a part via search query (if the part is available). put the country\'s alpha-2 code (e.g. uk, fr, es) if you wish to see pricing in other regions. only works for supported countries on pcpartpicker. use ,regions to see a full list of supported regions as well as their alpha-2 codes.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partprice(self, ctx, region, *, search_term=None):
        countries = [*self.bot.countries]
        await log(self.bot, 'partprice', ctx)

        if region.lower() in countries:
            search_string = search_term
            country = f"{region.lower()}."
        else:
            if search_term is None: search_string = region
            else: search_string = f"{region} {search_term}"
            country = ''

        embed_msg = discord.Embed(title=f"Finding pricing for '{search_string}' on PCPartPicker...",
                                  timestamp=datetime.utcnow(), colour=green)
        message = await ctx.send(embed=embed_msg)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, search_string)
        if len(productnames) == 0:
            embed_msg = discord.Embed(title=f"No results found for '{search_string}'.", colour=green, timestamp=datetime.utcnow())
            await message.edit(embed=embed_msg)
            return
        if len(productnames) == 1:
            product_url = f"https://{country}pcpartpicker.com{producturls[0]}"
        elif productnames == 'use_current':
            product_url = f"https://{country}pcpartpicker.com/search/?q={search_string}"
        else:
            slices = [f"{i + 1}. [{productnames[i]}]({f'https://{country}pcpartpicker.com{producturls[i]}'})" for i in
                      range(len(productnames)) if i < 10]
            while True:
                total = sum([len(item) for item in slices])
                if total < 1900:
                    break
                slices.pop(-1)
            description = '\n'.join(slices)
            embed_msg = discord.Embed(title=f"Showing results for {search_term}:", description=description,
                                      colour=green, timestamp=datetime.utcnow())
            await message.edit(embed=embed_msg)

            for i in range(len(slices)):
                await message.add_reaction(self.bot.reactions[i])

            await message.add_reaction(self.bot.reactions[-1])

            def check(reaction, user):
                return user == ctx.message.author and str(reaction.emoji) in self.bot.reactions and reaction.message == message
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            except asyncio.TimeoutError:
                embed_msg = discord.Embed(title="Timed out.", colour=green, timestamp=datetime.utcnow())
                await message.edit(embed=embed_msg)
                try:
                    await message.clear_reactions()
                except:
                    pass
                return

            if not str(reaction.emoji) == self.bot.reactions[-1]:
                product_url = f"https://{country}pcpartpicker.com{producturls[self.bot.reactions.index(str(reaction.emoji))]}"
            else:
                await message.delete()
                return

        with concurrent.futures.ThreadPoolExecutor() as pool:
            prices, links, sellers, images, stock, product_name = await asyncio.get_event_loop().run_in_executor(pool, get_price, product_url)

        if len(prices) > 0:
            formatted_pricing = '\n'.join([f"**[{sellers[i]}]({links[i]}): {prices[i]}**" if stock[i] == "In stock" else f"[{sellers[i]}]({links[i]}): {prices[i]}" for i in range(len(prices))])
        else:
            formatted_pricing = "No pricing available."

        if country == '':
            embed_msg = discord.Embed(title=f"Pricing for '{product_name}' in US:", description=formatted_pricing, timestamp=datetime.utcnow(), url=product_url.replace(' ', '+'), colour=green)
        else:
            embed_msg = discord.Embed(title=f"Pricing for '{product_name}' in {country.upper()[:-1]}:", description=formatted_pricing, timestamp=datetime.utcnow(), url=product_url.replace(' ', '+'), colour=green)

        if len(images) > 0:
            embed_msg.set_thumbnail(url=f"https:{images[0]}")

        await message.edit(embed=embed_msg)
        
        try:
            await message.clear_reactions()
        except:
            pass


    @commands.command(aliases=['psc', 'specscustom', 'sc'], description='shows detailed specs for a part via pcpartpicker link.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def partspecscustom(self, ctx, url):
        await log(self.bot, 'partspecscustom', ctx)
        global rate_limited
        if rate_limited == "1":
            embed_msg = discord.Embed(title="Finding specs...", timestamp=datetime.utcnow(), colour=green)
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
                    embed_msg = discord.Embed(title=name, description=description, colour=green,
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
                        colour=green, timestamp=datetime.utcnow())
                    await message.edit(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: partspecscustom")
            except requests.exceptions.MissingSchema:
                embed_msg = discord.Embed(title=f"No results found for {url}.", colour=green, timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by PCPartPicker')
                await message.edit(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.",
                                      colour=green, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild != None and message.guild.id == 246414844851519490:
            return
        elif message.author.id in (769886576321888256, 785613577066119229):
            return
        elif 'updatebuild' in message.content or 'createbuild' in message.content:
            return
        if not 'https://' in message.content and not 'pcpartpicker.com/list/' in message.content:
            return

        '''
        credit to CorpNewt for this regex: https://github.com/corpnewt/CorpBot.py/blob/rewrite/Cogs/Server.py#L20
        '''
        find = re.compile(r"(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")


        matches = [match.group() for match in re.finditer(find, message.content)]
        urls = []

        for match in matches:
            if '/product/' in match:
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    product_name, compatible_links, best_price, image = await asyncio.get_event_loop().run_in_executor(pool, format_product_link, match)

                embed_msg = discord.Embed(
                    title = product_name,
                    description = '\n'.join(compatible_links[:7]),
                    url = match,
                    colour = green
                )
                if best_price != None:
                    embed_msg.add_field(
                        name = "Best Price",
                        value = f"**{best_price[1]}: {best_price[0]}**"
                    )
                else:
                    embed_msg.add_field(
                        name = "Best Price",
                        value = f"Product not in stock."
                    )
                if image != None:
                    embed_msg.set_thumbnail(url=image)
                await message.channel.send(embed=embed_msg)
                continue
            if match.endswith("/list") or match.endswith("/list/"):
                if len(matches) > 1:
                    continue
                embed_msg = discord.Embed(
                    title = "You copied the wrong link for your PCPartPicker list!",
                    colour = green
                )
                embed_msg.set_image(url = "https://imgur.com/a/XrY2ClY")
                await message.channel.send(message.author.mention, embed=embed_msg)
                continue
            urls.append(match)

        if len(urls) == 0:
            return

        for url in urls:

            with concurrent.futures.ThreadPoolExecutor() as pool:
                products, total_wattage, total_price, page_title = await asyncio.get_event_loop().run_in_executor(pool, format_pcpp_link, url)

            if len(products) == 0:
                return

            description = '\n'.join([f"**{type}** - [{name}]({url})" if url != None else f"**{type}** - {name}" for type, name, url in products]) + '\n'
            if len(description) > 1950:
                description = '\n'.join([f"**{type}** - {name}" for type, name, url in products])[:1950] + '\n'

            if total_wattage != None:
                description += f"\n**Estimated Wattage:** {total_wattage}"
            if total_price != None and len(total_price) > len(products):
                description += f"\n**Total Price:** {total_price[-1]}"

            if page_title == "System Builder":
                page_title = "Parts List"

            embed_msg = discord.Embed(
                title = page_title,
                description = description,
                colour = green,
                url = url
            )
            await message.channel.send(embed=embed_msg)


    @commands.command()
    async def regions(self, ctx):
        description = '\n'.join([f"**{code.upper()}:** {self.bot.countries[code]}" for code in self.bot.countries])
        embed_msg = discord.Embed(
            title="Supported Regions",
            description=description,
            colour=green,
            timestamp=datetime.utcnow()
        )
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
                                          colour=green, timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
                worked = False

            if worked is True:
                embed_msg = discord.Embed(title=f"Fetching guides...",
                                          colour=green, timestamp=datetime.utcnow())
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
                                              colour=green, timestamp=datetime.utcnow(), url=url)
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
                        embed_msg = discord.Embed(title=f"'{message.content[1:]}' is not a number!", colour=green,
                                                  timestamp=datetime.utcnow())
                        await send.edit(embed=embed_msg)
                        worked = False
                    if worked is True:

                        embed_msg = discord.Embed(title=f"Fetching build...",
                                                  colour=green, timestamp=datetime.utcnow())
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
                                                          colour=green, timestamp=datetime.utcnow(),
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
                                    colour=green, timestamp=datetime.utcnow())
                                await send.edit(content="", embed=embed_msg)
                                quake = self.bot.get_user(405798011172814868)
                                await quake.send(f"Captcha Needed, bot down. Command: buildguides.")
                else:
                    db = open("scrapedata.txt", "w")
                    db.write("0")
                    rate_limited = "0"
                    embed_msg = discord.Embed(
                        title="Sorry, it seems like I am being rate limited. Please try again later.",
                        colour=green, timestamp=datetime.utcnow())
                    await ctx.send(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: buildguides.")

        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=green, timestamp=datetime.utcnow())
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
                        embeds.append(discord.Embed(title=f"Price trends for '{part}':", description=titles_list[i], colour=green,
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
                        colour=green, timestamp=datetime.utcnow())
                    await ctx.send(embed=embed_msg)
                    quake = self.bot.get_user(405798011172814868)
                    await quake.send(f"Captcha Needed, bot down. Command: trends")

            else:
                parts_list = "".join([f"- `{s}`\n" for s in parts])
                embed_msg = discord.Embed(title=f"'{part}' is not a supported part!",
                                          colour=green,
                                          timestamp=datetime.utcnow())
                embed_msg.add_field(name='Supported Parts:', value=parts_list, inline=False)
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=green, timestamp=datetime.utcnow())
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
                    embed_msg = discord.Embed(title="Select Subforum:", description=description, colour=green,
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
                    embed_msg = discord.Embed(title="", description=description, colour=green,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                    await ctx.send(embed=embed_msg)
                    embed_msg = discord.Embed(title="",
                                              colour=green,
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
                        embed_msg = discord.Embed(title=f"'{message.content[1:]}' is not a number!", colour=green,
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
                                colour=green,
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
                                                          colour=green,
                                                          timestamp=datetime.utcnow(), url=link_used)
                                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            else:
                                for i in range(len(titles)):
                                    if description == '':
                                        description = f"{i + 1}. [{titles[i]}]({links[i]})"
                                    else:
                                        description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                                embed_msg = discord.Embed(title=f"Posts in {titlesog[item]}:", description=description,
                                                          colour=green,
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
                                                          colour=green,
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
                                                              colour=green,
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
                                        colour=green, timestamp=datetime.utcnow())
                                    embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                                    await ctx.send(embed=embed_msg)
                                    quake = self.bot.get_user(405798011172814868)
                                    await quake.send(f"Captcha Needed, bot down. Command: pcppforums")
                            else:
                                embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=green,
                                                          timestamp=datetime.utcnow())
                                embed_msg.set_footer(name='Powered by pcpartpicker.com/forums')
                                await message.edit(embed=embed_msg)

                        else:
                            db = open("scrapedata.txt", "w")
                            db.write("0")
                            rate_limited = "0"
                            embed_msg = discord.Embed(
                                title="Sorry, it seems like I am being rate limited. Please try again later.",
                                colour=green, timestamp=datetime.utcnow())
                            embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                            await ctx.send(embed=embed_msg)
                            quake = self.bot.get_user(405798011172814868)
                            await quake.send(f"Captcha Needed, bot down. Command: pcppforums")

                    except ValueError:
                        embed_msg = discord.Embed(title=f"'{item}' is an invalid number!", colour=green,
                                                  timestamp=datetime.utcnow())
                        embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                        await ctx.send(embed=embed_msg)

            else:
                db = open("scrapedata.txt", "w")
                db.write("0")
                rate_limited = "0"
                embed_msg = discord.Embed(
                    title="Sorry, it seems like I am being rate limited. Please try again later.",
                    colour=green, timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by pcpartpicker.com/forums')
                await ctx.send(embed=embed_msg)
                quake = self.bot.get_user(405798011172814868)
                await quake.send(f"Captcha Needed, bot down. Command: pcppforums")

        else:
            embed_msg = discord.Embed(
                title="Sorry, it seems like I am being rate limited. Please try again later.",
                colour=green, timestamp=datetime.utcnow())
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
                                          timestamp=datetime.utcnow(), colour=green)
            except ValueError:
                embed_msg = discord.Embed(title=f"'{rank}' is not a number between 1 and 4!",
                                          timestamp=datetime.utcnow(), colour=green)
            except IndexError:
                embed_msg = discord.Embed(title=f"'{rank}' is not a number between 1 and 4!",
                                          timestamp=datetime.utcnow(), colour=green)
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title=f"You don't have permission to use that command!", colour=green,
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
                embed_msg = discord.Embed(title=tiers[i], description=descs[i], colour=green, timestamp=datetime.utcnow())
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

            embed_msg = discord.Embed(title=tiers[tier], description=descs[tier], colour=green,
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
                embed_msg = discord.Embed(title=f"Deleted case '{case_name}'.", colour=green, timestamp=datetime.utcnow())
            else:
                embed_msg = discord.Embed(title=f"Case with name '{case_name}' not found.", colour=green,
                                          timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title=f"You don't have permission to use that command!", colour=green,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    # @commands.command()
    # async def overview(self, ctx, *, part):
    #     global rate_limited
    #     if rate_limited == "1":
    #         embed_msg = discord.Embed(title=f"Finding info for '{part}' on PCPartPicker...", colour=green, timestamp=datetime.utcnow())
    #         send = await ctx.send(embed=embed_msg)
    #         with concurrent.futures.ThreadPoolExecutor() as pool:
    #             productnames, producturls = await asyncio.get_event_loop().run_in_executor(pool, query, part)
    #         if productnames == "rate_limited":
    #             db = open("scrapedata.txt", "w")
    #             db.write("0")
    #             rate_limited = "0"
    #             embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.", colour=green, timestamp=datetime.utcnow())
    #             await send.edit(embed=embed_msg)
    #             quake = self.bot.get_user(405798011172814868)
    #             await quake.send(f"Captcha Needed, bot down. Command: overview, {part}")
    #             return
    #         elif len(productnames) == 0:
    #             embed_msg = discord.Embed(title=f"No results found for '{part}'.", colour=green, timestamp=datetime.utcnow())
    #             await send.edit(embed=embed_msg)
    #         elif not productnames == "rate_limited" and len(productnames) > 0:
    #             description = '\n'.join([f"{i+1}. [{productnames[i]}]({f'https://pcpartpicker.com{producturls[i]}'})" for i in range(len(productnames))])
    #             embed_msg = discord.Embed(title=f"Showing results for {part}:", description=description, colour=green)
    #             embed_msg.set_footer(text="Powered by PCPartPicker")
    #             await send.edit(embed=embed_msg)
    #             reactions = ["1\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "2\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "3\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "4\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "5\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "6\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "7\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "8\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "9\N{variation selector-16}\N{combining enclosing keycap}",
    #                          "\N{keycap ten}",
    #                          "\u274C"]
    #
    #             if len(listofchoices) > 10:
    #                 listofchoices = listofchoices[:9]
    #
    #             for i in range(len(listofchoices)):
    #                 await message.add_reaction(reactions[i])
    #
    #             await message.add_reaction(reactions[-1])
    #
    #             def check(reaction, user):
    #                 return user == ctx.message.author and str(reaction.emoji) in reactions
    #
    #             reaction, user = await self.bot.wait_for('reaction_add', check=check)
    #
    #             if not str(reaction.emoji) == reactions[-1]:
    #                 item = reactions.index(str(reaction.emoji))
    #             else:
    #                 embed_msg = discord.Embed(title=f"Operation Cancelled.", colour=green)
    #                 embed_msg.set_footer(text="Powered by PCPartPicker")
    #                 return
    #     else:
    #         embed_msg = discord.Embed(title="Sorry, it seems like I am being rate limited. Please try again later.", colour=green, timestamp=datetime.utcnow())
    #         embed_msg.set_footer(text="Powered by PCPartPicker")
    #         await ctx.send(embed=embed_msg)



    @commands.command()
    async def refreshcountries(self, ctx):
        page = requests.get("https://pcpartpicker.com")
        soup = BeautifulSoup(page.content, "html.parser")
        selector = soup.find(class_="select select--small language-selector pp-country-select")
        slices = [slice for slice in str(selector).split('\n') if not "<select" in slice and not "</select" in slice]
        country_data = {}
        for slice in slices:
            country_data[slice.split('"')[-2]] = slice.replace("<", ">").split(">")[2]
        formatted_json = json.dumps(country_data, indent=4)
        await ctx.author.send(f"```json\n{formatted_json}```")
        with open("countries.json", "w") as file:
            file.write(formatted_json)
        bot.countries = country_data
        bot.urls = [f"https://{reg_code}.pcpartpicker.com" for reg_code in [*self.bot.countries]] + ["https://pcpartpicker.com/list/"]
        await ctx.send(embed=discord.Embed(title="Countries updated", colour=green))

    @commands.group(invoke_without_command=True)
    async def autopcpp(self, ctx):
        embed_msg = discord.Embed(
            title = "Toggle automatic PCPartPicker parts list and product link formatting",
            description = "Usage: `,autopcpp (enable|disable)`",
            colour = green
        )
        await ctx.send(embed=embed_msg)

    @autopcpp.command()
    async def enable(self, ctx):
        embed_msg = discord.Embed(
            description = "Auto PCPartPicker link formatting is now **enabled**.",
            colour = green
        )
        await ctx.send(embed=embed_msg)

    @autopcpp.command()
    async def disable(self, ctx):
        embed_msg = discord.Embed(
            description = "Auto PCPartPicker link formatting is now **disabled**.",
            colour = green
        )
        await ctx.send(embed=embed_msg)



def setup(bot):
    bot.add_cog(PCPartPicker(bot))