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
import aiosqlite
import random
import json
from pypartpicker import Scraper, get_list_links


green = discord.Colour(0x1e807c)
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.63', 'cookie': 'xsessionid=8gxgh7l25gwr276aregdd4qnj7zhmxwb; xcsrftoken=o7wXfkFMvIMf5SKShBaC4E0KJ7anQ1mdzHuZ4G6sWwMH2gSbcsZn5YdneEKo8fiv; xgdpr-consent=allow; __cfduid=d8b6350b0033bccdde51da015aaf07f381611344324; cf_clearance=d8b834d4bd7bf761c45622d38c027bc6e0d93f24-1612772344-0-150'}
allowed_ids = [405798011172814868, 370611001948635157, 287256464047865857, 454186048721780751, 191280151084924928, 698634807143563424, 411274336847134730, 479319375149662209, 750353117698064497, 629736214345416734, 746775313593270352]

def query(search_term):
    page = requests.get(f"https://pcpartpicker.com/search/?q={search_term}", headers=headers)
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

    page = requests.get(url, headers=headers)
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
    page = requests.get(url, headers=headers)
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



async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title=f"Command '{command}' used by {str(ctx.message.author)}.", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=green, timestamp=datetime.utcnow())
    await logs.send(embed=embed_msg)



def get_build_guides(url):

    page = requests.get(url, headers=headers)
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
    page = requests.get(url, headers=headers)
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

    page = requests.get(f"https://pcpartpicker.com/forums/", headers=headers)

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

    page = requests.get(url, headers=headers)
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
    page = requests.get(url, headers=headers)

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



async def update_db(**kwargs):
    id = kwargs.get("id")
    async with aiosqlite.connect("bot.db") as conn:
        if kwargs.get("action") == "remove":
            cursor = await conn.execute("DELETE FROM autopcpp WHERE guildid = ?", (id,))
        elif kwargs.get("action") == "add":
            cursor = await conn.execute("INSERT INTO autopcpp VALUES (?)", (id,))
        await conn.commit()



class PCPartPicker(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dequeue_urls.start()



    @tasks.loop(seconds=random.uniform(5.0, 10.0))
    async def dequeue_urls(self):
        if not self.bot.rate_limited:
            return
        if len(self.bot.queued_lists) > 0:
            self.dequeue_urls.change_interval(seconds=random.uniform(5.0, 10.0))
        else:
            self.dequeue_urls.change_interval(seconds=1)
            return
        list_item = self.bot.queued_lists[0]
        self.bot.queued_lists.pop(0)

        pcpp = Scraper()

        try:
            pcpp_list = pcpp.fetch_list(list_item[0])
        except pypartpicker.Verification as error:
            user = self.bot.get_user(405798011172814868)
            await user.send(f"```{error}```")
            return

        if len(pcpp_list.parts) == 0:
            return

        description = '\n'.join([f"**{part.type}** - [{part.name}]({part.url})" if part.url != None else f"**{part.type}** - {part.name}" for part in pcpp_list.parts]) + '\n'
        if len(description) > 1950:
            description = '\n'.join([f"**{part.type}** - {part.name}" for part in pcpp_list.parts])[:1950] + '\n'

        description += f"\n**Estimated Wattage:** {pcpp_list.wattage}"
        description += f"\n**Total Price:** {pcpp_list.total}"


        embed_msg = discord.Embed(
            title = "Parts List",
            description = description,
            colour = green,
            url = pcpp_list.url
        )

        await list_item[1].reply(embed=embed_msg)





    @commands.command(aliases=['specs', 'ps', 's'], description='shows detailed specs for a part via search query. if multiple results are returned, user must react with appropriate emoji to get the desired term.')
    @commands.cooldown(2, 120, commands.BucketType.member)
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
    @commands.cooldown(2, 120, commands.BucketType.member)
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




    @commands.Cog.listener()
    async def on_message(self, message):
        if not 'pcpartpicker' in message.content:
            return
        if message.author.id in (769886576321888256, 785613577066119229):
            return
        elif message.guild != None and message.guild.id in self.bot.autopcpp_disabled:
            return
        elif 'updatebuild' in message.content or 'createbuild' in message.content:
            return


        matches = get_list_links(message.content)


        urls = []

        for match in matches:
            if not 'pcpartpicker.com' in match and not '/list' in match:
                continue
            if match.endswith("/list") or match.endswith("/list/"):
                if len(matches) > 1:
                    continue
                embed_msg = discord.Embed(
                    title = "You copied the wrong link for your PCPartPicker list!",
                    colour = green
                )
                embed_msg.set_image(url = "https://images-ext-2.discordapp.net/external/d_524-5pqtAyimIrQTDWPumbJ-rB5JmglIR1UD9G8hI/https/i.imgur.com/zQrtYKAh.jpg")
                await message.reply(embed=embed_msg)
                continue
            urls.append((match, message))

        if len(urls) == 0:
            return

        for url in urls:
           self.bot.queued_lists.append(url)


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



    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def trends(self, ctx, *, part='cpu'):
        parts = ['cpu', 'memory', 'monitor', 'power supply', 'storage', 'video card']

        if not part.lower() in parts:
            parts_list = "".join([f"- `{s}`\n" for s in parts])
            embed_msg = discord.Embed(title=f"'{part}' is not a supported part!",
                                      colour=green,
                                      timestamp=datetime.utcnow())
            embed_msg.add_field(name='Supported Parts:', value=parts_list, inline=False)
            await ctx.send(embed=embed_msg)
            return
        url = f"https://pcpartpicker.com/trends/price/{part.replace(' ', '-')}/"

        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')

        images = []
        titles = []

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
                embed_msg = discord.Embed(title=f"Deleted case '{case_name}'.", colour=green, timestamp=datetime.utcnow())
            else:
                embed_msg = discord.Embed(title=f"Case with name '{case_name}' not found.", colour=green,
                                          timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title=f"You don't have permission to use that command!", colour=green,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)


    @commands.command()
    async def refreshcountries(self, ctx):
        if not ctx.author.id in self.bot.botadmins:
            embed_msg = discord.Embed(
                title = "You don't have permission to use that command!",
                colour = green
            )
            await ctx.send(embed=embed_msg)
            return
        page = requests.get("https://pcpartpicker.com", headers=headers)
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
        self.bot.countries = country_data
        self.bot.urls = [f"https://{reg_code}.pcpartpicker.com" for reg_code in [*self.bot.countries]] + ["https://pcpartpicker.com/list/"]
        await ctx.send(embed=discord.Embed(title="Countries updated", colour=green))


    @commands.group(invoke_without_command=True)
    async def autopcpp(self, ctx):
        embed_msg = discord.Embed(
            title = "Toggle automatic PCPartPicker parts list and product link formatting",
            description = "Usage: `,autopcpp (enable|disable)`",
            colour = green
        )
        await ctx.send(embed=embed_msg)


    @commands.has_permissions(manage_guild=True)
    @autopcpp.command()
    async def enable(self, ctx):

        if not ctx.guild.id in self.bot.autopcpp_disabled:
            embed_msg = discord.Embed(
                description="You already have auto PCPartPicker formatting enabled!",
                colour=green
            )
            await ctx.send(embed=embed_msg)
            return
        self.bot.autopcpp_disabled.remove(ctx.guild.id)
        await update_db(action="remove", id=ctx.guild.id)
        embed_msg = discord.Embed(
            description = "Auto PCPartPicker link formatting is now **enabled**.",
            colour = green
        )
        await ctx.send(embed=embed_msg)


    @commands.has_permissions(manage_guild=True)
    @autopcpp.command()
    async def disable(self, ctx):

        if ctx.guild.id in self.bot.autopcpp_disabled:
            embed_msg = discord.Embed(
                description="You already have auto PCPartPicker formatting disabled!",
                colour=green
            )
            await ctx.send(embed=embed_msg)
            return

        self.bot.autopcpp_disabled.append(ctx.guild.id)
        await update_db(action="add", id=ctx.guild.id)
        embed_msg = discord.Embed(
            description = "Auto PCPartPicker link formatting is now **disabled**.",
            colour = green
        )
        await ctx.send(embed=embed_msg)



def setup(bot):
    bot.add_cog(PCPartPicker(bot))