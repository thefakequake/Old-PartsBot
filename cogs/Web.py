import praw
import re
import discord
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType
import math
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
import concurrent.futures
import asyncio
import DiscordUtils
import json

file = open("credentials.json")

data = json.load(file)

file.close()

reddit_details = praw.Reddit(client_id=data["client_id"], client_secret=data["client_secret"], username=data["username"],
                     password=data["password"], user_agent='praw thing')

apexstats_api_key = data["TRN-Api-Key"]

subs = ['pcmasterrace', 'buildapc', 'buildapcsales', 'corsair', 'razer', 'intel', 'amd', 'ayymd', 'mechanicalkeyboards',
        'nvidia', 'phanteks', 'battlestations', 'pcgaming', 'gamingpc', 'watercooling', 'overclocking', 'sffpc', 'nzxt',
        'hackintosh', 'monitors', 'pcbuild', 'hardware', 'linustechtips', 'raspberry_pi', 'python', 'cats']

red = discord.Colour.from_rgb(0, 100, 0)


async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title=f"Command '{command}' used by {str(ctx.message.author)}.", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=red, timestamp=datetime.utcnow())
    await logs.send(embed=embed_msg)



def get_subforums():
    links = []
    titles = []

    page = requests.get(f"https://linustechtips.com/")

    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.find_all(class_='ipsDataItem_title ipsType_break'):
        titles.append(a.get_text().replace('\n', ''))

    for a in soup.find_all(href=True):
        if a['href'][0:32] == 'https://linustechtips.com/forum/':
            for i in titles:
                if i.replace(' ', '-').replace(',', '').replace('@', '').lower() in a['href']:
                    links.append(a['href'])

    links = list(dict.fromkeys(links))
    return links, titles

def get_posts(url):
    page = requests.get(url)
    links = []
    titles = []
    description = ''
    soup = BeautifulSoup(page.content, 'html.parser')
    for a in soup.find_all(class_='ipsType_break ipsContained cTopicTitle'):
        for i in a.get_text():
            titles.append(a.get_text().replace('\t', '').replace('\n', ''))

    for a in soup.find_all(href=True):
        if a['href'][0:32] == 'https://linustechtips.com/topic/':
            if not a['href'][-10:-1] == '/#comment':
                if not a['href'][-15:] == '=getLastComment':
                    if not a['href'][-14:] == '=getNewComment':
                        if not '?do=findComment&comment=' in a['href']:
                            links.append(a['href'])

    links = list(dict.fromkeys(links))
    titles = list(dict.fromkeys(titles))
    return links, titles




def get_post(url):
    content = []
    details = []
    page = requests.get(url)

    soup = BeautifulSoup(page.content, 'html.parser')
    for a in soup.find_all(class_='cPost_contentWrap'):
        for i in a.get_text():
            content.append(a.get_text().replace('\t', '').replace('\n', ' ').replace('\xa0', ''))
    for a in soup.find_all(class_='ipsType_blendLinks'):
        details.append(a.get_text())
    content = list(dict.fromkeys(content))
    return content, details





class Web(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['ltt', 'lf', 'lmgforums', 'lttforum', 'lmgforum'],
                 description='sends posts from linustechtips.com in the subforum of your choice. if no subforum name or index is given, the entire subforum list is sent and users are able to choose which one they want to view.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def lttforums(self, ctx, *, forum=None):
        await log(self.bot, 'lttforums', ctx)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            links, titles = await asyncio.get_event_loop().run_in_executor(pool, get_subforums)
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
            embed_msg.set_footer(text='Powered by linustechtips.com')
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
            embed_msg.set_footer(text='Powered by linustechtips.com')
            await ctx.send(embed=embed_msg)
            embed_msg = discord.Embed(title="",
                                      description="Send ',' and then the corresponding number of the subforum in chat.\nE.g, `,10`.",
                                      colour=red,
                                      timestamp=datetime.utcnow())
            embed_msg.set_footer(text='Powered by linustechtips.com')
            await ctx.send(embed=embed_msg)

            def check(message):
                return len(message.content) > 0 and message.content[0] == ',' and message.channel == ctx.message.channel

            message = await self.bot.wait_for('message', check=check)
            try:
                item = int(message.content[1:]) - 1
            except ValueError:
                embed_msg = discord.Embed(title=f"'{message.content[1:]}' is not a number!", colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by linustechtips.com')
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
                        title=f"No forum found with index or name '{forum}'. Use `,lttforums` for a full list of forums.",
                        colour=red,
                        timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by linustechtips.com')
                    await ctx.send(embed=embed_msg)
                    attempt = 'failed'
        if not attempt == 'failed':
            try:
                titlesog = titles
                link_used = links[item]
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    links, titles = await asyncio.get_event_loop().run_in_executor(pool, get_posts, links[item])
                description = ''
                if len(titles) > 10:
                    for i in range(10):
                        if description == '':
                            description = f"{i + 1}. [{titles[i]}]({links[i]})"
                        else:
                            description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                    embed_msg = discord.Embed(title=f"Posts in {titlesog[item]}:", description=description, colour=red,
                                              timestamp=datetime.utcnow(), url=link_used)
                else:
                    for i in range(len(titles)):
                        if description == '':
                            description = f"{i + 1}. [{titles[i]}]({links[i]})"
                        else:
                            description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
                    embed_msg = discord.Embed(title=f"Posts in {titlesog[item]}:", description=description, colour=red,
                                              timestamp=datetime.utcnow(), url=link_used)
                embed_msg.set_footer(text='Powered by linustechtips.com')
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
                    embed_msg.set_footer(text='Powered by linustechtips.com')
                    await message.edit(embed=embed_msg)
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        content, details = await asyncio.get_event_loop().run_in_executor(pool, get_post, links[item])
                    contenttodisplay = content[0]
                    if len(contenttodisplay) > 2040:
                        contenttodisplay = f"{contenttodisplay[0:2040]}..."
                    embed_msg = discord.Embed(title=titles[item], description=f"{contenttodisplay}", colour=red,
                                              timestamp=datetime.utcnow(), url=links[item])
                    embed_msg.set_footer(text='Powered by linustechtips.com')
                    embed_msg.add_field(name='Extra Details', value="Posted by " + details[1].replace('\n', '') + ".",
                                        inline=False)
                    await message.edit(embed=embed_msg)
                else:
                    embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by linustechtips.com')
                    await message.edit(embed=embed_msg)
            except ValueError:
                embed_msg = discord.Embed(title=f"'{item}' is an invalid number!", colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by linustechtips.com')

                await ctx.send(embed=embed_msg)

    @commands.command(
        description='sends a random post from a subreddit of your choice (has to be in the supported list to avoid abuse of the command). if no subreddit is given, a random one is chosen from the list.')
    @commands.cooldown(3, 20, commands.BucketType.member)
    async def randompost(self, ctx, subreddit=None):
        await log(self.bot, 'randompost', ctx)
        global subs
        worked = False
        if subreddit is None:
            worked = True
            subreddit_name = subs[random.randint(0, len(subs) - 1)]
        elif subreddit in subs:
            subreddit_name = subreddit
            worked = True
        elif subreddit.replace('r/', '') in subs:
            subreddit_name = subreddit.replace('r/', '')
            worked = True
        elif subreddit.replace('/r/', '') in subs:
            subreddit_name = subreddit.replace('/r/', '')
            worked = True
        else:
            description = ''
            for sub in subs:
                if description == '':
                    description = f"**{sub}**"
                else:
                    description = f"{description}, **{sub}**"
            embed_msg = discord.Embed(title=f"'{subreddit}' is an invalid subreddit!",
                                      description=f"To prevent people from abusing this command, the only subreddits you may use are as follows:\n\n{description}\n\nIf you have any suggestions for subreddits to add, please contact QuaKe#5943 with a tech (preferably PC related) subreddit.",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        if worked is True:
            global reddit_details
            sub = reddit_details.subreddit(subreddit_name)
            hot = sub.hot(limit=None)
            image = False
            if subreddit is None:
                posts = [post for post in sub.hot(limit=40)]
            else:
                posts = [post for post in sub.hot(limit=40)]
            random_post_number = random.randint(0, 39)
            random_post = posts[random_post_number]
            while str(random_post.url).startswith("https://v.redd.it/"):
                random_post_number = random.randint(0, 19)
                random_post = posts[random_post_number]
            url = str(random_post.url)
            content = str(random_post.selftext).replace('&#x200B;', '')
            title = str(random_post.title)
            if len(content) > 2000:
                content = f"{content[0:2000]}..."
            if url.endswith("jpg") or url.endswith("jpeg") or url.endswith("png") or url.endswith(
                    "mp4") or url.endswith("gif") or url.endswith("mov") or url.startswith("https://gfycat.com/"):
                image = True
            embed_msg = discord.Embed(title=title, description=content, colour=red, timestamp=datetime.utcnow(),
                                      url="https://www.reddit.com" + random_post.permalink)
            embed_msg.add_field(name=f'Posted by u/{str(random_post.author.name)}',
                                value=f"{random_post.score} upvotes, {int(random_post.upvote_ratio * 100)}% upvoted.",
                                inline=False)
            embed_msg.set_footer(text=f'r/{subreddit_name}')
            if image is True:
                embed_msg.set_image(url=url)
            await ctx.send(embed=embed_msg)

    @commands.command(
        description='browses reddit.com in a subreddit of your choice (has to be in the supported list to prevent abuse of the command). if no subreddit is given, a random subreddit is picked.')
    @commands.cooldown(2, 20, commands.BucketType.member)
    async def reddit(self, ctx, subreddit=None):
        await log(self.bot, 'reddit', ctx)
        global subs
        worked = False
        if subreddit is None:
            worked = True
            subreddit_name = subs[random.randint(0, len(subs) - 1)]
        elif subreddit in subs:
            subreddit_name = subreddit
            worked = True
        elif subreddit.replace('r/', '') in subs:
            subreddit_name = subreddit.replace('r/', '')
            worked = True
        elif subreddit.replace('/r/', '') in subs:
            subreddit_name = subreddit.replace('/r/', '')
            worked = True
        else:
            description = ''
            for sub in subs:
                if description == '':
                    description = f"**{sub}**"
                else:
                    description = f"{description}, **{sub}**"
            embed_msg = discord.Embed(title=f"'{subreddit}' is an invalid subreddit!",
                                      description=f"To prevent people from abusing this command, the only subreddits you may use are as follows:\n\n{description}\n\nIf you have any suggestions for subreddits to add, please contact QuaKe#5943 with a tech (preferably PC related) subreddit.",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        if worked is True:
            global reddit_details
            sub = reddit_details.subreddit(subreddit_name)
            posts = sub.hot(limit=10)
            postobjects = [post for post in sub.hot(limit=20)]
            description = ''
            titles = []
            links = []
            for post in posts:
                titles.append(post.title)
                links.append('https://www.reddit.com' + post.permalink)
            for i in range(0, len(links)):
                if description == '':
                    description = f"{i + 1}. [{titles[i]}]({links[i]})"
                else:
                    description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"
            embed_msg = discord.Embed(title=f"Posts on r/{subreddit_name}:",
                                      description=description,
                                      colour=red, timestamp=datetime.utcnow())
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
                image = False
                url = postobjects[item].url
                content = str(postobjects[item].selftext)
                if url.endswith("jpg") or url.endswith("jpeg") or url.endswith("png") or url.endswith(
                        "mp4") or url.endswith("gif") or url.endswith("mov") or url.startswith("https://gfycat.com/"):
                    image = True
                embed_msg = discord.Embed(title=titles[item], description=content, colour=red,
                                          timestamp=datetime.utcnow(),
                                          url=links[item])
                embed_msg.add_field(name=f'Posted by u/{str(postobjects[item].author.name)}',
                                    value=f"{postobjects[item].score} upvotes, {int(postobjects[item].upvote_ratio * 100)}% upvoted.",
                                    inline=False)
                embed_msg.set_footer(text=f'r/{subreddit_name}')
                if image is True:
                    embed_msg.set_image(url=url)
                await message.edit(embed=embed_msg)
            else:
                embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                          timestamp=datetime.utcnow())
                await message.edit(embed=embed_msg)

    @commands.command(description='sends the geekbench leaderboards.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def geekbench(self, ctx):

        await log(self.bot, 'geekbench', ctx)

        reactions = ["1\N{variation selector-16}\N{combining enclosing keycap}",
                     "2\N{variation selector-16}\N{combining enclosing keycap}",
                     "3\N{variation selector-16}\N{combining enclosing keycap}",
                     "4\N{variation selector-16}\N{combining enclosing keycap}",
                     "5\N{variation selector-16}\N{combining enclosing keycap}",
                     "6\N{variation selector-16}\N{combining enclosing keycap}",
                     "7\N{variation selector-16}\N{combining enclosing keycap}",
                     "8\N{variation selector-16}\N{combining enclosing keycap}", "\u274C"]

        embed_msg = discord.Embed(title=f"Select Leaderboard:",
                                  description='''1. [Android](https://browser.geekbench.com/android-benchmarks)
                                                  2. [iOS](https://browser.geekbench.com/ios-benchmarks)
                                                  3. [Mac](https://browser.geekbench.com/mac-benchmarks)
                                                  4. [Processor](https://browser.geekbench.com/processor-benchmarks)
                                                  5. [CUDA](https://browser.geekbench.com/cuda-benchmarks)
                                                  6. [Metal](https://browser.geekbench.com/metal-benchmarks)
                                                  7. [OpenCL](https://browser.geekbench.com/opencl-benchmarks)
                                                  8. [Vulcan](https://browser.geekbench.com/vulkan-benchmarks)
                                                  ''', timestamp=datetime.utcnow(),
                                  colour=red)

        # noinspection PyRedundantParentheses
        data = (('Android Benchmarks', 'https://browser.geekbench.com/android-benchmarks', ('Yes', '/android_devices/'),
                 'Single Core', 'Multi Core'),
                ('iOS Benchmarks', 'https://browser.geekbench.com/ios-benchmarks', ('Yes', '/ios_devices/'),
                 'Single Core', 'Multi Core', 'Metal'),
                ('Mac Benchmarks', 'https://browser.geekbench.com/mac-benchmarks', ('Yes', '/macs/'), 'Single Core',
                 'Multi Core'),
                ('Processor Benchmarks', 'https://browser.geekbench.com/processor-benchmarks', ('Yes', '/processors/'),
                 'Single Core', 'Multi Core'),
                ('CUDA Benchmarks', 'https://browser.geekbench.com/cuda-benchmarks', ('No')),
                ('Metal Benchmarks', 'https://browser.geekbench.com/metal-benchmarks', ('No')),
                ('OpenCL Benchmarks', 'https://browser.geekbench.com/opencl-benchmarks', ('No')),
                ('Vulcan Benchmarks', 'https://browser.geekbench.com/vulkan-benchmarks', ('No')))

        item2 = 0

        embed_msg.set_footer(text='Powered by browser.geekbench.com')

        message = await ctx.send(embed=embed_msg)

        for reaction in reactions:
            await message.add_reaction(reaction)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in reactions

        reaction, user = await self.bot.wait_for('reaction_add', check=check)

        item = 0

        if not str(reaction.emoji) == reactions[-1]:
            item = reactions.index(str(reaction.emoji))

        if not str(reaction.emoji) == reactions[-1]:

            page = requests.get(data[item][1])
            soup = BeautifulSoup(page.content, 'html.parser')

            pagetitle = ''
            titles = []
            links = []
            scores = []

            for title in soup.find_all(class_='page-header'):
                pagetitle = f"{title.get_text()} ".replace('\n', '')

            if data[item][2][0] == 'Yes':

                for url in soup.find_all(href=True):
                    if url['href'].startswith(data[item][2][1]):
                        links.append(url['href'])
                        titles.append(url.get_text().replace('\n', ''))

            else:
                for title in soup.find_all(class_='name'):
                    if not title.get_text() == 'Device':
                        titles.append(title.get_text().replace('\n', ''))

            for score in soup.find_all(class_='score'):
                if not score.get_text() == 'Score':
                    scores.append(score.get_text().replace('\n', ''))

            lowest_score = 999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999

            do = True

            starts = [0]

            if len(data[item]) > 3:
                for i in range(len(scores)):
                    if int(scores[i]) < lowest_score or int(scores[i]) == lowest_score:
                        lowest_score = int(scores[i])
                    else:
                        starts.append(i)
                        lowest_score = int(scores[i])

                reactions = ["1\N{variation selector-16}\N{combining enclosing keycap}",
                             "2\N{variation selector-16}\N{combining enclosing keycap}",
                             "3\N{variation selector-16}\N{combining enclosing keycap}",
                             "4\N{variation selector-16}\N{combining enclosing keycap}",
                             "5\N{variation selector-16}\N{combining enclosing keycap}",
                             "6\N{variation selector-16}\N{combining enclosing keycap}",
                             "7\N{variation selector-16}\N{combining enclosing keycap}",
                             "8\N{variation selector-16}\N{combining enclosing keycap}", "\u274C"]

                description = ''

                for i in range(len(data[item]) - 3):

                    if description == '':

                        description = f"{i + 1}. {data[item][i + 3]}"

                    else:

                        description = f"{description}\n{i + 1}. {data[item][i + 3]}"

                embed_msg = discord.Embed(title="Select Category:", description=description, colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by browser.geekbench.com')

                thebot = self.bot.get_user(743378829304922113)

                try:
                    await message.clear_reactions()
                except:
                    for reaction in reactions:
                        try:
                            await message.remove_reaction(reaction, thebot)
                        except:
                            pass

                await message.edit(embed=embed_msg)

                for i in range(len(data[item]) - 3):
                    await message.add_reaction(reactions[i])

                await message.add_reaction(reactions[-1])

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in reactions

                reaction, user = await self.bot.wait_for('reaction_add', check=check)

                if not str(reaction.emoji) == reactions[-1]:
                    item2 = reactions.index(str(reaction.emoji))
                else:
                    item2 = 'stop'
                    embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by browser.geekbench.com')
                    await message.edit(embed=embed_msg)

            if not item2 == 'stop':

                item2 = int(item2)

                links = links[starts[item2]:]
                titles = titles[starts[item2]:]
                scores = scores[starts[item2]:]

                if len(links) > 0:

                    links = [f"https://browser.geekbench.com{link}" for link in links]

                else:

                    links = [f"https://browser.geekbench.com" for i in range(len(titles))]

                if pagetitle.endswith(' '):
                    pagetitle = pagetitle[:-2]

                rounds = 0
                embeds = []

                if len(data[item]) > 3:
                    embed_msg = discord.Embed(title=f"{pagetitle}: {data[item][item2 + 3]}", colour=red,
                                              timestamp=datetime.utcnow(), url=data[item][1])
                    embed_msg.set_footer(text='Powered by browser.geekbench.com')
                else:
                    embed_msg = discord.Embed(title=f"{pagetitle}", colour=red,
                                              timestamp=datetime.utcnow(), url=data[item][1])
                    embed_msg.set_footer(text='Powered by browser.geekbench.com')

                skips = 0
                for i in range(80):
                    if rounds == 8:
                        skips += 1
                        embeds.append(embed_msg)
                        embed_msg = ''
                        rounds = 0
                        if len(data[item]) > 3:
                            embed_msg = discord.Embed(title=f"{pagetitle}: {data[item][item2 + 3]}", colour=red,
                                                      timestamp=datetime.utcnow(), url=data[item][1])
                            embed_msg.set_footer(text='Powered by browser.geekbench.com')
                        else:
                            embed_msg = discord.Embed(title=f"{pagetitle}", colour=red,
                                                      timestamp=datetime.utcnow(), url=data[item][1])
                            embed_msg.set_footer(text='Powered by browser.geekbench.com')
                    else:
                        embed_msg.add_field(name=f'⠀', value=f'**{i - skips + 1}**')
                        embed_msg.add_field(name=f'⠀', value=f'[{titles[i - skips]}]({links[i - skips]})')
                        embed_msg.add_field(name=f'⠀', value=f'**{scores[i - skips]}**')

                        rounds += 1

                await message.delete()

                paginator = DiscordUtils.Pagination.CustomEmbedPaginator(ctx, timeout=30)
                paginator.add_reaction('⏪', "back")
                paginator.add_reaction('⏩', "next")
                paginator.add_reaction('❌', "lock")

                await paginator.run(embeds)

        else:

            embed_msg = discord.Embed(title="Operation cancelled.", colour=red,
                                      timestamp=datetime.utcnow())
            embed_msg.set_footer(text='Powered by browser.geekbench.com')
            await message.edit(embed=embed_msg)

    @commands.command(description='browses products on novelkeys.xyz')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def novelkeys(self, ctx, *, searchterm):

        await log(self.bot, 'novelkeys', ctx)

        embed_msg = discord.Embed(title=f"Searching for '{searchterm}' on Novelkeys...", colour=red,
                                  timestamp=datetime.utcnow())
        embed_msg.set_footer(text='Powered by novelkeys.xyz')
        message = await ctx.send(embed=embed_msg)

        url = f'https://novelkeys.xyz/search?page=1&q={searchterm}&type=product'

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        titles = []
        links = []
        images = []

        for img in soup.find_all('img', src=True):
            if img['src'].startswith('//cdn.shopify.com/s/files/') and '/products/' in img['src']:
                images.append(f"https:{img['src']}")

        for title in soup.find_all(href=True):
            if title['href'].startswith('/products/') and not title['href'] == '/products/':
                links.append(f"https://novelkeys.xyz{title['href']}")
                titles.append(title.get_text().replace('\n', ''))

        if len(titles) > 0:

            if len(titles) > 1:
                description = ''

                for i in range(len(titles)):
                    if not i > 10:
                        if description == '':
                            description = f"{i + 1}. [{titles[i]}]({links[i]})"
                        else:
                            description = f"{description}\n{i + 1}. [{titles[i]}]({links[i]})"

                embed_msg = discord.Embed(title=f"Results for '{searchterm}' on Novelkeys:", description=description,
                                          colour=red,
                                          timestamp=datetime.utcnow())
                embed_msg.set_footer(text='Powered by novelkeys.xyz')
                await message.edit(embed=embed_msg)

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

                for i in range(len(titles)):
                    await message.add_reaction(reactions[i])

                await message.add_reaction(reactions[-1])

                def check(reaction, user):
                    return user == ctx.message.author and str(reaction.emoji) in reactions

                reaction, user = await self.bot.wait_for('reaction_add', check=check)

                if not str(reaction.emoji) == reactions[-1]:
                    item = reactions.index(str(reaction.emoji))
                else:
                    item = 'stop'
                    embed_msg = discord.Embed(title="Operation cancelled.", description="", colour=red,
                                              timestamp=datetime.utcnow())
                    embed_msg.set_footer(text='Powered by novelkeys.xyz')
                    await message.edit(embed=embed_msg)


            else:
                item = 0

            page = requests.get(links[item])
            soup = BeautifulSoup(page.content, 'html.parser')

            descriptions = []
            images = []
            prices = []

            for img in soup.find_all('img', src=True):
                if img['src'].startswith('//cdn.shopify.com/s/files/') and '/products/' in img['src']:
                    images.append(f"https:{img['src']}")

            for text in soup.find_all(class_="product-single__description rte"):
                descriptions.append(text.get_text().replace('\xa0', ' '))

            for text in soup.find_all(class_="btn product-form__cart-submit"):
                button = text.get_text().replace('\n', '')

            if 'Add to cart' in button:
                for text in soup.find_all(class_="price-item price-item--regular"):
                    prices.append(text.get_text().replace('\n', ''))

            content = descriptions[0].split('\n')

            for text in content:
                if text == '\n' or text == '':
                    content.pop(content.index(text))

            description = ''

            for text in content[1:]:
                if description == '':
                    description = f"{text}"
                else:
                    description = f"{description}\n{text}"

            description = description.replace('\n', '   ')

            embed_msg = discord.Embed(title=titles[item], colour=red,
                                      timestamp=datetime.utcnow(), url=links[item])
            if len(description) > 1024:
                description = f"{description[:1000]}..."
            if len(prices) > 0:
                embed_msg.add_field(name=content[0], value=f"{description}\n\n**{prices[0]}**")
            else:
                embed_msg.add_field(name=content[0], value=f"{description}\n\n**Out of stock**")
            embed_msg.set_footer(text='Powered by novelkeys.xyz')
            embed_msg.set_thumbnail(url=images[0])
            await message.edit(embed=embed_msg)

        else:

            embed_msg = discord.Embed(title=f"No results found for '{searchterm}'.", colour=red,
                                      timestamp=datetime.utcnow())
            embed_msg.set_footer(text='Powered by novelkeys.xyz')
            await message.edit(embed=embed_msg)

    @commands.command(description='sends apex legends statistics for players on pc, xbox or playstation.')
    @commands.cooldown(2, 60, commands.BucketType.member)
    async def apexstats(self, ctx, platform, *, user):
        global apexstats_api_key
        platformnumber = 0

        pcalises = ['pc', 'origin', 'desktop']
        psaliases = ['ps', 'playstation', 'ps4', 'psn', 'ps5', 'pls', 'play']
        xbxaliases = ['xbox', 'xb', 'xboxone', 'xbox', 'xbx', 'x', 'xbo', 'box']

        if str(platform).lower() in pcalises:
            platformnumber = '5'
        elif str(platform).lower() in psaliases:
            platformnumber = '2'
        elif str(platform).lower() in xbxaliases:
            platformnumber = '1'

        if not platformnumber == 0:
            try:
                headers = {'TRN-Api-Key': apexstats_api_key}

                page = requests.get(f"https://public-api.tracker.gg/v2/apex/standard/profile/{platformnumber}/{user}",
                                    headers=headers)

                database = page.json()

                playerdata = {}

                try:
                    playerdata["profileurl"] = database['data']['platformInfo']['avatarUrl']
                except:
                    pass

                try:
                    playerdata["profileuserid"] = database['data']['platformInfo']['platformUserId']
                except:
                    pass

                try:
                    playerdata["profileuserhandle"] = database['data']['platformInfo']['platformUserHandle']
                except:
                    pass

                try:
                    playerdata["profileuseridentifier"] = database['data']['platformInfo']['platformUserIdentifier']
                except:
                    pass

                try:
                    playerdata["platform"] = database['data']['platformInfo']['platformSlug']
                except:
                    pass

                try:
                    playerdata["countrycode"] = database['data']['userInfo']['countryCode']
                except:
                    pass

                try:
                    playerdata["rankname"] = database['data']['segments'][0]['stats']['rankScore']['metadata'][
                        'rankName']
                except:
                    pass

                try:
                    playerdata["rankurl"] = database['data']['segments'][0]['stats']['rankScore']['metadata']['iconUrl']
                except:
                    pass

                try:
                    playerdata["activelegendname"] = database['data']['metadata']['activeLegendName']
                except:
                    pass

                try:
                    playerdata["level"] = database['data']['segments'][0]['stats']['level']['displayValue']
                except:
                    pass

                try:
                    playerdata["kills"] = database['data']['segments'][0]['stats']['kills']['displayValue']
                except:
                    pass

                try:
                    playerdata["winningkills"] = database['data']['segments'][0]['stats']['winningKills'][
                        'displayValue']
                except:
                    pass

                try:
                    playerdata["damage"] = database['data']['segments'][0]['stats']['damage']['displayValue']
                except:
                    pass

                try:
                    playerdata["matchesplayed"] = database['data']['segments'][0]['stats']['matchesPlayed'][
                        'displayValue']
                except:
                    pass

                try:
                    playerdata["timesplacedtop3"] = database['data']['segments'][0]['stats']['timesPlacedtop3'][
                        'displayValue']
                except:
                    pass

                embed_msg = discord.Embed(title="Apex Legends Statistics", colour=red, timestamp=datetime.utcnow())
                embed_msg.set_author(name=playerdata["profileuseridentifier"], icon_url=playerdata["profileurl"])
                embed_msg.set_footer(text="Powered by apex.tracker.gg")

                try:
                    embed_msg.add_field(name="Country", value=playerdata["countrycode"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Platform", value=playerdata["platform"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Rank", value=playerdata["rankname"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Active Legend Name", value=playerdata["activelegendname"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Level", value=playerdata["level"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Matches Played", value=playerdata["matchesplayed"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Times Placed Top 3", value=playerdata["timesplacedtop3"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Kills", value=playerdata["kills"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Winning Kills", value=playerdata["winningkills"], inline=False)
                except:
                    pass

                try:
                    embed_msg.add_field(name="Damage", value=playerdata["damage"], inline=False)
                except:
                    pass

                try:
                    embed_msg.set_thumbnail(url=playerdata["rankurl"])
                except:
                    pass

                await ctx.send(embed=embed_msg)



            except KeyError:
                embed_msg = discord.Embed(title=f"User '{user}' not found.",
                                          description='Double check their username and that you are checking on the correct platform.',
                                          colour=red, timestamp=datetime.utcnow())
                embed_msg.set_footer(text="Powered by apex.tracker.gg")
                await ctx.send(embed=embed_msg)

        else:
            embed_msg = discord.Embed(title=f"'{platform}' is an invalid platform!",
                                      description='Make sure you are using one of the following platforms:\n\nPC\nXbox\nPlaystation',
                                      colour=red, timestamp=datetime.utcnow())
            embed_msg.set_footer(text="Powered by apex.tracker.gg")
            await ctx.send(embed=embed_msg)







def setup(bot):
    bot.add_cog(Web(bot))