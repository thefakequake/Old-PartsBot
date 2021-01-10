import discord
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import BucketType
from datetime import datetime
import concurrent.futures
import asyncio
import random
from bs4 import BeautifulSoup
import requests
import os
from fuzzywuzzy import process
import json
import aiosqlite

with open("credentials.json") as file:
    data = json.load(file)
    file.close()

red = discord.Colour.from_rgb(0, 100, 0)
error_colour = discord.Colour.from_rgb(254, 0, 0)
yellow = discord.Colour.from_rgb(254, 254, 0)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(help_command=None, command_prefix=commands.when_mentioned_or(data["command_prefix"]), intents=intents, case_insensitive=True)



@bot.event
async def on_ready():
    bannedcogs = []
    if bot.user.id == 785613577066119229:
        bannedcogs = ['News', 'Poll']
    print('PartsBot is starting...')
    for filename in os.listdir("cogs"):
        if filename.endswith(".py") and not filename.replace('.py', '') in bannedcogs:
            name = filename.replace(".py", "")
            bot.load_extension(f"cogs.{name}")
            print(f"cogs.{name} loaded")
    print("PartsBot is ready.")
    channel = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title="Bot restarted.", colour=red, timestamp=datetime.utcnow())
    await channel.send(embed=embed_msg)
    while True:
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=",help"))
        await asyncio.sleep(60)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} servers."))
        await asyncio.sleep(30)
        members = 0
        for guild in bot.guilds:
            members += guild.member_count
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{members} users."))
        await asyncio.sleep(30)


@bot.command()
async def load(ctx, cog):
    if ctx.author.id in (287256464047865857, 405798011172814868):
        if cog.lower() == 'all':
            for filename in os.listdir("cogs"):
                if filename.endswith(".py"):
                    name = filename.replace(".py", "")
                    bot.load_extension(f"cogs.{name}")
            embed_msg = discord.Embed(title=f"Sucessfully loaded all cogs.",
                                      colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            try:
                bot.load_extension(f"cogs.{cog}")
                embed_msg = discord.Embed(title=f"Sucessfully loaded the cog '{cog}'.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionNotFound:
                embed_msg = discord.Embed(title=f"Cog '{cog}' not found.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionAlreadyLoaded:
                embed_msg = discord.Embed(title=f"Cog is already loaded!",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)

    else:
        embed_msg = discord.Embed(title="You don't have permission to use this command!",
                                  colour=red,
                                  timestamp=datetime.utcnow())
        await ctx.send(embed=embed_msg)

@bot.command(aliases=['re'])
async def reload(ctx, cog):
    if ctx.author.id in (287256464047865857, 405798011172814868):
        if cog.lower() == 'all':
            for filename in os.listdir("cogs"):
                if filename.endswith(".py"):
                    name = filename.replace(".py", "")
                    bot.reload_extension(f"cogs.{name}")
            embed_msg = discord.Embed(title=f"Sucessfully reloaded all cogs.",
                                      colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            try:
                bot.reload_extension(f"cogs.{cog}")
                embed_msg = discord.Embed(title=f"Sucessfully reloaded the cog '{cog}'.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionNotFound:
                embed_msg = discord.Embed(title=f"Cog '{cog}' not found.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionNotLoaded:
                embed_msg = discord.Embed(title=f"Cog is not loaded!",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)

    else:
        embed_msg = discord.Embed(title="You don't have permission to use this command!",
                                  colour=red,
                                  timestamp=datetime.utcnow())
        await ctx.send(embed=embed_msg)

@bot.command(aliases=['un'])
async def unload(ctx, cog):
    if ctx.author.id in (287256464047865857, 405798011172814868):
        if cog.lower() == 'all':
            for filename in os.listdir("cogs"):
                if filename.endswith(".py"):
                    name = filename.replace(".py", "")
                    bot.unload_extension(f"cogs.{name}")
            embed_msg = discord.Embed(title=f"Sucessfully unloaded all cogs.",
                                      colour=red,
                                      timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            try:
                bot.unload_extension(f"cogs.{cog}")
                embed_msg = discord.Embed(title=f"Sucessfully unloaded the cog '{cog}'.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionNotFound:
                embed_msg = discord.Embed(title=f"Cog '{cog}' not found.",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)
            except discord.ext.commands.ExtensionNotLoaded:
                embed_msg = discord.Embed(title=f"Cog is already unloaded!",
                                          colour=red,
                                          timestamp=datetime.utcnow())
                await ctx.send(embed=embed_msg)

    else:
        embed_msg = discord.Embed(title="You don't have permission to use this command!",
                                  colour=red,
                                  timestamp=datetime.utcnow())
        await ctx.send(embed=embed_msg)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed_msg = discord.Embed(title=str(error), timestamp=datetime.utcnow(), colour=red)
        await ctx.send(embed=embed_msg)
        return
    if isinstance(error, commands.MissingRequiredArgument):
        embed_msg = discord.Embed(title="Missing Required Argument!", description=f"You are seeing this error because the command you are trying to use needs more information to function.\nType `,help [name of command]` to see usage for that command.", timestamp=datetime.utcnow(), colour=red)
        await ctx.send(embed=embed_msg)
        return
    if isinstance(error, commands.CommandNotFound):
        commandslist = [command.name for command in bot.commands]
        command = ctx.message.content[1:].split(" ")
        highest = process.extractOne(command[0], commandslist)
        if int(highest[1]) > 80:
            embed_msg = discord.Embed(title=f"Command '{command[0]}' not found.", description=f'Perhaps you meant \'**{highest[0]}**\'.', timestamp=datetime.utcnow(), colour=red)
            await ctx.send(embed=embed_msg)
        return
    if isinstance(error, commands.MissingPermissions):
        embed_msg = discord.Embed(title="Missing Permissions!", description=str(error), timestamp=datetime.utcnow(), colour=red)
        await ctx.send(embed=embed_msg)
        return
    embed_msg = discord.Embed(title="Oops! Something went wrong...", description="Looks like I've encountered an error. I have sent a bug report to the [PartsBot Discord](https://discord.gg/WM9pHp8).")
    channel = bot.get_channel(773989689060229180)
    embed_msg = discord.Embed(title=f"Error: {str(error)}", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=error_colour, timestamp=datetime.utcnow())
    await channel.send(embed=embed_msg)



@bot.event
async def on_guild_join(guild):
    worked = False
    for channel in guild.channels:
        if worked is False:
            try:
                embed_msg = discord.Embed(title='Thanks for adding PartsBot to your server!', colour=red,
                                          timestamp=datetime.utcnow())

                embed_msg.add_field(name='Here\'s a few things you can try:',
                                    value='''

                - Sending a PCPartPicker list
                - Doing `,partspecs [name of part]`
                - Doing `,partprice [name of part]`
                - Doing `,randompost`
                If you need additional help, join the [Offical Discord](https://discord.gg/WM9pHp8) or contact **QuaKe#5943**.
                ''')
                await channel.send(embed=embed_msg)
                worked = True
            except:
                pass


bot.run(data["token"])

