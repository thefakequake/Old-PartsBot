import asyncio
import discord

from currency_converter import CurrencyConverter
from datetime import datetime
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from google_trans_new import google_translator
from google_trans_new import constant


red = discord.Colour(0x1e807c)

# Instantiate required objects
translator = google_translator()
c = CurrencyConverter()

# Obtain dictionary containing all languages supported by google_trans_new
supp_languages = constant.LANGUAGES


async def log(bot, command, ctx):
    logs = bot.get_channel(769906608318316594)
    embed_msg = discord.Embed(
        title=f"Command '{command}' used by {str(ctx.message.author)}.",
        description=f"**Text:**\n{ctx.message.content}\n\n"
                    f"**User ID:**\n{ctx.author.id}\n\n"
                    f"**Full Details:**\n{str(ctx.message)}",
        colour=red,
        timestamp=datetime.utcnow()
    )
    await logs.send(embed=embed_msg)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description='translates text from one language into another.'
    )
    @commands.cooldown(2, 20, commands.BucketType.member)
    async def translate(self, ctx, source_lang: str, target_lang: str, *,
                        text: str):
        await log(self.bot, 'translate', ctx)

        try:
            translation = translator.translate(
                text,
                lang_src=source_lang,
                lang_tgt=target_lang
            )
            embed_msg = discord.Embed(
                title="Translation Result",
                description=translation,
                colour=red,
                timestamp=datetime.utcnow()
            )
            embed_msg.set_footer(text='Powered by Google Translate')
            await ctx.send(embed=embed_msg)
        except ValueError:
            embed_msg = discord.Embed(
                title="Invalid language!",
                description="Please use `,languages` for a list of supported "
                            "languages.\nCommand usage: `,translate "
                            "(language 1) (language 2) (text)`",
                colour=red,
                timestamp=datetime.utcnow()
            )
            embed_msg.set_footer(text='Powered by Google Translate')
            await ctx.send(embed=embed_msg)

    @commands.command(
        description='DMs user a list of supported languages for the '
                    ',translate command.'
    )
    async def languages(self, ctx):
        embed_msg = discord.Embed(
            title="Supported Languages",
            description="\n".join(
                "{}: {}".format(*p) for p in sorted(supp_languages.items())
            ),
            colour=red,
            timestamp=datetime.utcnow()
        )
        await ctx.author.send(embed=embed_msg)
        await ctx.message.add_reaction('📨')

    @commands.command(description='converts from one currency to another.')
    @commands.cooldown(2, 20, commands.BucketType.member)
    async def convert(self, ctx, amount: float, source_cur: str,
                      target_cur: str):
        await log(self.bot, 'convert', ctx)

        source_cur = source_cur.upper()
        target_cur = target_cur.upper()

        try:
            conversion = c.convert(
                amount,
                source_cur,
                target_cur
            )
            embed_msg = discord.Embed(
                title="Conversion Result",
                description="**{}** {} is **{:.2f}** {}.".format(
                    amount,
                    source_cur,
                    conversion,  # :.2f sets the precision to 2 decimal places
                    target_cur
                ),
                colour=red,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed_msg)
        except ValueError:
            embed_msg = discord.Embed(
                title="Invalid currency or number!",
                description="Please use `,currencies` for a list of supported "
                            "currencies.\nCommand usage: `,convert (amount) "
                            "(currency 1) (currency 2)`",
                colour=red,
                timestamp=datetime.utcnow()
            )
            await ctx.send(embed=embed_msg)

    @commands.command(
        description='DMs user a list of supported currencies for the '
                    ',convert command.'
    )
    async def currencies(self, ctx):
        embed_msg = discord.Embed(
            title="Supported Currencies",
            description="AUD Australian dollar\n"
                        "BGN Bulgarian lev\n"
                        "BRL Brazilian real\n"
                        "CAD Canadian dollar\n"
                        "CHF Swiss franc\n"
                        "CNY Chinese yuan renminbi\n"
                        "CZK Czech koruna\n"
                        "DKK Danish krone\n"
                        "GBP Pound sterling\n"
                        "HKD Hong Kong dollar\n"
                        "HRK Croatian kuna\n"
                        "HUF Hungarian forint\n"
                        "IDR Indonesian rupiah\n"
                        "ILS Israeli shekel\n"
                        "INR Indian rupee\n"
                        "ISK Icelandic krona\n"
                        "JPY Japanese yen\n"
                        "KRW South Korean won\n"
                        "MXN Mexican peso\n"
                        "MYR Malaysian ringgit\n"
                        "NOK Norwegian krone\n"
                        "NZD New Zealand dollar\n"
                        "PHP Philippine peso\n"
                        "PLN Polish zloty\n"
                        "RON Romanian leu\n"
                        "RUB Russian rouble\n"
                        "SEK Swedish krona\n"
                        "SGD Singapore dollar\n"
                        "THB Thai baht\n"
                        "TRY Turkish lira\n"
                        "USD US dollar\n"
                        "ZAR South African rand",
            colour=red,
            timestamp=datetime.utcnow()
        )
        await ctx.author.send(embed=embed_msg)
        await ctx.message.add_reaction('📨')

    @commands.command()
    async def timer(self, ctx, time: str):
        symbols = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }
        worked = False
        failed = False

        try:
            for symbol in symbols:
                if symbol in time:
                    conversion = symbols[symbol]
                    timeperiod = int(time.replace(symbol, '')) * conversion
                    worked = True
        except ValueError:
            embed_msg = discord.Embed(
                title=f"'{time}' is an invalid time period!",
                description="Please only use whole numbers, and the following "
                            "symbols:\n"
                            "```s: seconds\n"
                            "m: minutes\n"
                            "h: hours\n"
                            "d: days```\n"
                            "Example: `,timer 10m`",
                colour=red
            )
            await ctx.send(embed=embed_msg)
            failed = True

        if worked is True:
            if not timeperiod > 1209600:
                if timeperiod > 59:
                    strtime = str(round(timeperiod / 60, 1))
                    if strtime.endswith('.0'):
                        strtime = strtime[:-2]
                    if strtime == '1':
                        strtime = f"{strtime} minute"
                    else:
                        strtime = f"{strtime} minutes"

                if timeperiod > 3599:
                    strtime = str(round(timeperiod / 3600, 1))
                    if strtime.endswith('.0'):
                        strtime = strtime[:-2]
                    if strtime == '1':
                        strtime = f"{strtime} hour"
                    else:
                        strtime = f"{strtime} hours"

                if timeperiod > 86399:
                    strtime = str(round(timeperiod / 86400, 1))
                    if strtime.endswith('.0'):
                        strtime = strtime[:-2]
                    if strtime == '1':
                        strtime = f"{strtime} day"
                    else:
                        strtime = f"{strtime} days"

                if timeperiod < 60:
                    if timeperiod == 1:
                        strtime = f"{timeperiod} second"
                    else:
                        strtime = f"{timeperiod} seconds"

                embed_msg = discord.Embed(
                    title="Timer Started",
                    description=strtime,
                    colour=red
                )
                await ctx.send(embed=embed_msg)

                if timeperiod > 119:
                    await asyncio.sleep(timeperiod - 60)
                    await ctx.send(
                        f"{ctx.message.author.mention}, you have 60 seconds "
                        "left!"
                    )
                    await asyncio.sleep(60)
                    await ctx.send(
                        f"{ctx.message.author.mention}, your timer is up!"
                    )
                else:
                    await asyncio.sleep(timeperiod)
                    await ctx.send(
                        f"{ctx.message.author.mention}, your timer is up!"
                    )
            else:
                embed_msg = discord.Embed(
                    title="The maximum amount of time for a timer is 2 weeks!",
                    colour=red
                )
                await ctx.send(embed=embed_msg)
        elif failed is False:
            embed_msg = discord.Embed(
                title=f"'{time}' is an invalid time period!",
                description="Please only use whole numbers, and the following "
                            "symbols:\n"
                            "```s: seconds\n"
                            "m: minutes\n"
                            "h: hours\n"
                            "d: days```\n"
                            "Example: `,startgiveaway 10d nitro`",
                colour=red
            )
            await ctx.send(embed=embed_msg)


def setup(bot):
    bot.add_cog(Utility(bot))
