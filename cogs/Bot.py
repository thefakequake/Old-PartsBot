import discord
from discord.ext import commands, tasks
from datetime import datetime

red = discord.Colour(0x1e807c)

status_ids = [405798011172814868, 287256464047865857, 370611001948635157, 399672562788859906]

global last_restarted
last_restarted = datetime.utcnow()

async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(title=f"Command '{command}' used by {str(ctx.message.author)}.", description=f"**Text:**\n{ctx.message.content}\n\n**User ID:**\n{ctx.author.id}\n\n**Full Details:**\n{str(ctx.message)}", colour=red, timestamp=datetime.utcnow())
    await logs.send(embed=embed_msg)

class Bot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot



    @commands.command(aliases=['commands'], description='shows usage and description for command. if no command is put, sends all commands in a list.')
    async def help(self, ctx, commandhelp=None):
        try:
            if commandhelp is None:
                private_commands = ['leave', 'unlock', 'status', 'reload', 'unload', 'load']
                desc = ''
                commands_list = []
                commands = {name: [cmd.name for cmd in cog.walk_commands()] for name, cog in self.bot.cogs.items()}
                for command in commands:
                    if not desc == '':
                        desc = f"{desc}\n\n**{command}**"
                    else:
                        desc = f"{desc}\n**{command}**"
                    desc += f"\n{', '.join([f'`{command}`' for command in list(commands[command])])}"
                embed_msg = discord.Embed(title="Commands",
                                          description=f"Use `,help [command name]` to get more information on a specific command.\n{desc}\n\nIf you need extra help, join the [Official Discord](https://discord.gg/WM9pHp8) or contact **QuaKe#5943**.",
                                          timestamp=datetime.utcnow(), colour=red, url="https://discord.gg/xxzKRtm4nk")
                await ctx.send(embed=embed_msg)
            else:
                desc = self.bot.get_command(commandhelp)
                embed_msg = discord.Embed(title=f"{(desc.name)}",
                                          timestamp=datetime.utcnow(), colour=red, url="https://discord.gg/xxzKRtm4nk")
                embed_msg.add_field(name="Usage", value=f",{desc.name} {desc.signature}", inline=False)
                if not desc.description == '':
                    embed_msg.add_field(name="Description", value=f"{desc.description}", inline=False)
                else:
                    embed_msg.add_field(name="Description", value=f"(no description set)", inline=False)
                if desc.aliases != []:
                    embed_msg.add_field(name="Aliases", value=', '.join(desc.aliases), inline=False)
                await ctx.send(embed=embed_msg)
        except AttributeError:
            embed_msg = discord.Embed(title=f"Command '{commandhelp}' not found.", timestamp=datetime.utcnow(),
                                      colour=red)
            await ctx.send(embed=embed_msg)



    @commands.command(description='sends various bot statistics.')
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def stats(self, ctx):
        db = open("scrapedata.txt", "r")
        data = db.read()
        if data == '1':
            ratelimited = "False"
        else:
            ratelimited = "True"
        global last_restarted
        servers = len(self.bot.guilds)
        members = 0
        for guild in self.bot.guilds:
            members += guild.member_count
        private_commands = ['leave', 'unlock', 'status', 'reload', 'unload', 'load']
        commands_amount = 0
        for command in self.bot.commands:
            if not str(command.name) in private_commands:
                commands_amount += 1
        embed_msg = discord.Embed(title="Bot Stats",
                                  description=f"**Total server count:** {servers}\n**Total member count of servers:** {members}\n**Total public commands:** {commands_amount}\n**Total hidden commands:** {len(private_commands)}\n**PCPP rate limited?:** {ratelimited}\n**Bot ping:** {int(self.bot.latency * 1000)}ms\n**Bot last restarted:** {last_restarted.replace(microsecond=0)} GMT",
                                  timestamp=datetime.utcnow(), colour=red)
        await ctx.send(embed=embed_msg)



    @commands.command(description='sends bot information including invite link, official discord and credits.')
    async def info(self, ctx):
        embed_msg = discord.Embed(title="About PartsBot",
                                  description="PartsBot was created by QuaKe#5943.\nPartsBot scrapes [PCPartPicker](https://pcpartpicker.com/) and is programmed in Python with the [discord.py](https://github.com/Rapptz/discord.py) API wrapper.\n\n[Invite Link](https://discord.com/api/oauth2/authorize?client_id=769886576321888256&permissions=0&scope=bot) • [Official Discord Server](https://discord.gg/WM9pHp8) • [Patreon](https://patreon.com/partsbot) • [GitHub](https://github.com/QuaKe8782/PartsBot) • [DBL](https://discordbotlist.com/bots/partsbot) • [top.gg](https://top.gg/bot/769886576321888256)\n\nSpecial thanks to Bogdan, Duck Dude, Zorf, Ozone and John Benber.\nShout out to Grxffiti.",
                                  timestamp=datetime.utcnow(), colour=red)
        embed_msg.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{self.bot.user.id}/{self.bot.user.avatar}.png?size=1024")
        await ctx.send(embed=embed_msg)

        


    @commands.command(aliases=['pong'], description='sends current bot ping in milliseconds.')
    async def ping(self, ctx):
        embed_msg = discord.Embed(title="Ping", description=f"{int(self.bot.latency * 1000)}ms", colour=red,
                                  timestamp=datetime.utcnow())
        await ctx.send(embed=embed_msg)



    @commands.command(description='changes the bot\'s status.')
    async def status(self, ctx, *, status_name):
        global status_ids
        await log('status', ctx)
        if ctx.message.author.id in status_ids:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=status_name))
            embed_msg = discord.Embed(title="Successfully changed status to:", description=status_name,
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
        else:
            embed_msg = discord.Embed(title="You don't have permission to do that!",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 762381281287471144:
            role = member.guild.get_role(769989043311476736)
            await member.add_roles(role)

    @commands.command()
    async def leave(self, ctx):
        await log('leave', ctx)
        if ctx.author.id == 405798011172814868:
            embed_msg = discord.Embed(title="Goodbye!",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)
            await ctx.guild.leave()
        else:
            embed_msg = discord.Embed(title="You don't have permission to do that!",
                                      colour=red, timestamp=datetime.utcnow())
            await ctx.send(embed=embed_msg)

    @commands.command(description='sends partsbot\'s invite link.')
    async def invite(self, ctx):
        embed_msg = discord.Embed(title="PartsBot invite link",
                                  colour=red, timestamp=datetime.utcnow(), url='https://discord.com/api/oauth2/authorize?client_id=769886576321888256&permissions=0&scope=bot')
        embed_msg.add_field(name='Click the title to get redirected.', value='Use `,info` for additional bot information.')
        await ctx.send(embed=embed_msg)

    @commands.command(description='sends partsbot\'s github link.', aliases=['code', 'repo'])
    async def github(self, ctx):
        embed_msg = discord.Embed(title="PartsBot Github",
                                  colour=red, timestamp=datetime.utcnow(),
                                  url='https://github.com/QuaKe8782/PartsBot')
        embed_msg.add_field(name='Click the title to get redirected.',
                            value='Use `,info` for additional bot information.')
        await ctx.send(embed=embed_msg)

def setup(bot):
    bot.add_cog(Bot(bot))