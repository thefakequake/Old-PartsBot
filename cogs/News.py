import discord
from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands, tasks
import asyncio
from bs4 import BeautifulSoup
import json
import praw
from datetime import datetime
import requests
import aiosqlite

red = discord.Colour.from_rgb(0, 100, 0)

file = open("credentials.json")

data = json.load(file)

file.close()

reddit_details = praw.Reddit(client_id=data["client_id"], client_secret=data["client_secret"], username=data["username"],
                     password=data["password"], user_agent='praw thing')



def get_reddit_posts():
    
    global reddit_details
    sub = reddit_details.subreddit("technews")
    hot = sub.hot(limit=20)

    post_titles = []
    post_urls = []

    for post in hot:
        if not post.stickied:
            post_titles.append(str(post.title))
            post_urls.append("https://www.reddit.com" + post.permalink)

    description = ''

    for i in range(5):
        if not len(f"{description}\n\n- [{post_titles[i]}]({post_urls[i]})") > 1950:
            description = f"{description}\n\n- [{post_titles[i]}]({post_urls[i]})"

    embed = discord.Embed(title="r/technews", description=description, colour=red, timestamp=datetime.utcnow())
    embed.set_thumbnail(url=sub.icon_img)

    return embed


def get_hexus_posts():

    page = requests.get("https://hexus.net/")

    soup = BeautifulSoup(page.content, "html.parser")

    newstitles = []
    newslinks = []
    images = []

    for title in soup.find_all(href=True):
        if title['href'].startswith("/tech/news/"):
            if not title['href'] in newslinks and not title.get_text() == '\n' and not title.get_text() == ' NEW':
                newstitles.append(title.get_text())
                newslinks.append(f"https://hexus.net{title['href']}")


    description = ''

    if len(newstitles) > 0 and len(newslinks) > 0:

        for i in range(5):
            if not len(f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})") > 1950:
                description = f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})"

        embed = discord.Embed(title="hexus.net", description=description, colour=red, timestamp=datetime.utcnow())
        embed.set_thumbnail(url="https://hexus.net/media/img/hexus_web_shadow_trans.png?402516240412")

        return embed

    else:

        embed = discord.Embed(title="hexus.net", description="Sorry, something went wrong.", colour=red, timestamp=datetime.utcnow())
        return embed

def get_kitguru_posts():
    page = requests.get("https://www.kitguru.net/")

    soup = BeautifulSoup(page.content, "html.parser")

    newstitles = []
    newslinks = []

    for title in soup.find_all(href=True):
        if title['href'].startswith("https://www.kitguru.net/components/") and len(title.get_text()) > 8:
            newstitles.append(title.get_text())
            newslinks.append(title['href'])

    description = ''

    if len(newstitles) > 0 and len(newslinks) > 0:

        for i in range(5):
            if not len(f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})") > 1950:
                description = f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})"

        embed = discord.Embed(title="kitguru.net", description=description, colour=red, timestamp=datetime.utcnow())
        embed.set_thumbnail(url="https://www.kitguru.net/wp-content/uploads/2017/01/kg_logo3.png")

        return embed
    else:
        embed = discord.Embed(title="kitguru.net", description="Sorry, something went wrong.", colour=red,
                              timestamp=datetime.utcnow())
        return embed

def get_anandtech_posts():
    page = requests.get("https://www.anandtech.com/")

    soup = BeautifulSoup(page.content, "html.parser")

    newstitles = []
    newslinks = []

    for title in soup.find_all(href=True):
        if title['href'].startswith("/show/") and len(
                title.get_text()) > 8 and not 'Best' in title.get_text() and not '\n' in title.get_text() and not 'Comments' in title.get_text() and not 'comments' in title.get_text():
            if not title.get_text() in newstitles:
                newstitles.append(title.get_text())
                newslinks.append(f"https://anandtech.com{title['href']}")

    description = ''

    if len(newstitles) > 0 and len(newslinks) > 0:

        for i in range(5):
            if not len(f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})") > 1950:
                description = f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})"

        embed = discord.Embed(title="anandtech.com", description=description, colour=red, timestamp=datetime.utcnow())
        embed.set_thumbnail(url="https://www.anandtech.com/Content/images/logo2.png")

        return embed
    else:
        embed = discord.Embed(title="anandtech.com", description="Sorry, something went wrong.", colour=red, timestamp=datetime.utcnow())
        return embed



def get_lttforums_posts():
    page = requests.get("https://linustechtips.com/forum/13-tech-news/")

    newslinks = []
    newstitles = []

    soup = BeautifulSoup(page.content, 'html.parser')
    for a in soup.find_all(class_='ipsType_break ipsContained cTopicTitle'):
        for i in a.get_text():
            if not 'Posting Guidelines' in a.get_text():
                newstitles.append(a.get_text().replace('\t', '').replace('\n', ''))

    for a in soup.find_all(href=True):
        if a['href'][0:32] == 'https://linustechtips.com/topic/':
            if not a['href'][-10:-1] == '/#comment':
                if not a['href'][-15:] == '=getLastComment':
                    if not a['href'][-14:] == '=getNewComment':
                        if not '?do=findComment&comment=' in a['href']:
                            if not 'posting-guidelines' in a['href']:
                                newslinks.append(a['href'])

    newslinks = list(dict.fromkeys(newslinks))
    newstitles = list(dict.fromkeys(newstitles))

    if len(newslinks) > 0 and len(newstitles) > 0:

        description = ''

        for i in range(5):
            if not len(f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})") > 1950:
                description = f"{description}\n\n- [{newstitles[i]}]({newslinks[i]})"

        embed = discord.Embed(title="linustechtips.com", description=description, colour=red, timestamp=datetime.utcnow())
        embed.set_thumbnail(url="https://linustechtips.com/uploads/monthly_2020_11/LogoBanner.png.9dcbb8d14242568d3dada0426914390d.png")

        return embed

    else:

        embed = discord.Embed(title="linustechtips.com", description="Sorry, something went wrong.", colour=red,
                              timestamp=datetime.utcnow())
        return embed







class News(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=12)
    async def updatenews(bot):
        embeds = []
        channels = []

        def is_bot(message):
            return message.author == bot.user

        for i in (get_lttforums_posts(), get_reddit_posts(), get_hexus_posts(), get_kitguru_posts(), get_anandtech_posts()):
            embeds.append(i)

        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from subscriptions")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        for row in info:
            if row[1] != 'None':
                try:
                    channels.append(bot.get_channel(int(row[1])))
                except:
                    pass

        for channel in channels:
            await channel.purge(check=is_bot)
            for embed_msg in embeds:
                try:
                    await channel.send(embed=embed_msg)
                    await asyncio.sleep(2)
                except:
                    pass

    @commands.command(aliases=['addnewschannel'])
    @commands.has_permissions(manage_guild=True)
    async def setnewschannel(self, ctx):
        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from subscriptions")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        found = False
        alreadysetup = False
        for row in info:
            if row[0] == str(ctx.message.guild.id):
                found = True
                if row[1] != 'None':
                    alreadysetup = True
                    channelid = int(row[1])

        if alreadysetup is False:
            conn = await aiosqlite.connect("bot.db")
            if found is True:
                cursor = await conn.execute("UPDATE subscriptions SET newsid = ? WHERE guildid = ?", (str(ctx.message.channel.id), str(ctx.message.guild.id)))
            else:
                cursor = await conn.execute("INSERT INTO subscriptions VALUES (?, ?, ?)", (str(ctx.message.guild.id), str(ctx.message.channel.id), 'None'))
            await conn.commit()
            await conn.close()
            embed_msg = discord.Embed(title="News channel set up for this channel.", description=f"<#{ctx.message.channel.id}>\n\nUse `,removenewschannel` to remove it.", colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="There is already a news channel set up for this server!", description=f"<#{channelid}>\n\nUse `,removenewschannel` to remove it.", colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command(aliases=['deletenewschannel'])
    @commands.has_permissions(manage_guild=True)
    async def removenewschannel(self, ctx):
        conn = await aiosqlite.connect("bot.db")
        cursor = await conn.execute("SELECT * from subscriptions")
        info = await cursor.fetchall()
        await conn.commit()
        await conn.close()

        found = False
        alreadysetup = False
        for row in info:
            if row[0] == str(ctx.message.guild.id):
                found = True
                if row[1] != 'None':
                    alreadysetup = True
                    channelid = int(row[1])

        if found is True:
            if alreadysetup is True:
                conn = await aiosqlite.connect("bot.db")
                cursor = await conn.execute("UPDATE subscriptions SET newsid = ? WHERE guildid = ?", ('None', str(ctx.message.guild.id)))
                await conn.commit()
                await conn.close()

                embed_msg = discord.Embed(title="News channel for this server removed.", description='Use `,addnewschannel` in the channel you want to use to add one.', colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)

            else:
                embed_msg = discord.Embed(title="There is no news channel set up for this server!", colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="There is no news channel set up for this server!", colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

def setup(bot):
    News.updatenews.start(bot)
    bot.add_cog(News(bot))