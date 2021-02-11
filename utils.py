import discord
from discord.ext import commands
import ast
from fuzzywuzzy import process
import aiosqlite

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


class Part:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.id = kwargs.get("id")
        self.data = kwargs.get("data")
        self.db_obj = kwargs.get("db_obj")


    async def edit_spec(self, **kwargs):
        if kwargs.get("spec_name") is None:
            raise ValueError("No kwarg 'spec_name' passed!")
            return
        elif kwargs.get("spec_value") is None:
            raise ValueError("No kwarg 'spec_value' passed!")
            return
        elif not isinstance(kwargs.get("spec_value"), list):
            raise ValueError("Spec value must be a list!")
            return
        async with aiosqlite.connect(self.db_obj.db) as conn:
            cursor = await conn.execute("SELECT * FROM parts WHERE part_id = ?", (self.id,))
            part = await cursor.fetchone()
            await conn.commit()
        part_specs = ast.literal_eval(part[3])
        part_specs[kwargs.get("spec_name")] = kwargs.get("spec_value")
        async with aiosqlite.connect(self.db_obj.db) as conn:
            await conn.execute("UPDATE parts SET part_data = ? WHERE part_id = ?", (str(part_specs), self.id))
            await conn.commit()
        return part_specs


class Database:
    def __init__(self, db_name):
        self.db = db_name


    async def generate_id(self):
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.execute("SELECT * FROM count")
            count = await cursor.fetchone()
            await conn.execute("DELETE FROM count")
            await conn.execute("INSERT INTO count VALUES (?)", (count[0] + 1,))
            await conn.commit()
        return count[0] + 1


    async def add_part(self, **kwargs):
        async with aiosqlite.connect(self.db) as conn:
            id = await self.generate_id()
            await conn.execute("INSERT INTO parts VALUES (?, ?, ?, ?)", (id, kwargs.get("name", "None"), kwargs.get("type", "None").lower(), "{}"))
            await conn.commit()
        return id


    async def search_parts(self, **kwargs):
        async with aiosqlite.connect(self.db) as conn:
            if kwargs.get("type") is None:
                cursor = await conn.execute("SELECT part_name FROM parts")
            else:
                cursor = await conn.execute("SELECT part_name FROM parts WHERE part_type = ?", (kwargs.get("type").lower(),))
            part_names = [item[0] for item in await cursor.fetchall()]
            fuzzy_ratios = process.extract(kwargs.get("name"), part_names)
            strings = [ratio[0] for ratio in fuzzy_ratios[:20] if ratio[1] >= 60]
            pairs = []
            for string in strings:
                cursor = await conn.execute("SELECT part_id FROM parts WHERE part_name = ?", (string,))
                item = await cursor.fetchone()
                pairs.append((string, item[0]))
        return pairs


    async def fetch_part(self, id):
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.execute("SELECT * FROM parts WHERE part_id = ?", (id,))
            part = await cursor.fetchone()
            await conn.commit()
        if len(part) == 0:
            return None
        return Part(id = part[0], name = part[1], data = part[2], db_obj = self)