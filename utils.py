import discord
from discord.ext import commands


def get_member(guild, **attrs):
    name = attrs["name"]

    try:
        discriminator = attrs["discriminator"]
    except KeyError:
        discriminator = None

    user = f"{name}#{discriminator}" if discriminator else name

    for member in guild.members:
        if user.lower() in str(member).lower():
            return member


class Member(commands.MemberConverter):
    async def query_member_named(self, guild, argument):
        if len(argument) > 5 and argument[-5] == '#':
            username, _, discriminator = argument.rpartition('#')

            return get_member(guild, name=username, discriminator=discriminator)
        else:
            return get_member(guild, name=argument)
