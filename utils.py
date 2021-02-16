import discord
from discord.ext import commands
import json
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


class Database:
    def __init__(self, db_name):
        self.db = db_name


    async def _get_next_sequence_num(self):
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.execute("SELECT seq FROM sqlite_sequence WHERE name = ?", ("parts",))
            num = await cursor.fetchone()
            await conn.commit()
        return int(num[0]) + 1

    async def add_part(self, part_data):
        
        if part_data.get("name") is None or not isinstance(part_data.get("name"), str):
            raise ValueError("Key name is either missing or not str!")
        elif part_data.get("type") is None or not isinstance(part_data.get("type"), str):
            raise ValueError("Key type is either missing or not str!")
        elif part_data.get("manufacturer") is None or not isinstance(part_data.get("manufacturer"), str):
            raise ValueError("Key manufacturer is either missing or str!")
        elif part_data.get("specs") != None and not isinstance(part_data.get("specs"), dict):
            raise ValueError("Key specs must either be dict or None!")
        elif part_data.get("images") != None and not isinstance(part_data.get("images"), list):
            raise ValueError("Key images must either be list or None!")
        elif part_data.get("sources") != None and not isinstance(part_data.get("sources"), list):
            raise ValueError("Key sources must either be list or None!")
        elif part_data.get("notes") != None and not isinstance(part_data.get("notes"), list):
            raise ValueError("Key notes must either be list or None!")
        elif part_data.get("contributors") != None and not isinstance(part_data.get("contributors"), list):
            raise ValueError("Key contributors must either be list or None!")

        data = {
            "name": part_data.get("name"),
            "type": part_data.get("type"),
            "manufacturer": part_data.get("manufacturer"),
            "id": await self._get_next_sequence_num(),
            "specs": part_data.get("specs", {}),
            "images": part_data.get("images", []),
            "sources": part_data.get("sources", []),
            "notes": part_data.get("notes", [])
        }

        async with aiosqlite.connect(self.db) as conn:
            await conn.execute("INSERT INTO parts (part_name, part_type, part_data) VALUES (?, ?, ?)", (part_data["name"], part_data["type"].lower(), str(data)))
            cursor = await conn.execute("SELECT last_insert_rowid()")
            item = await cursor.fetchone()
            await conn.commit()
        return item[0]


    async def edit_part(self, id, dict):
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.execute("SELECT * FROM parts WHERE part_id = ?", (id,))
            part = await cursor.fetchone()
            if part is None:
                raise ValueError("Invalid part ID!")
            if dict["name"] != part[1]:
                await conn.execute("UPDATE parts SET part_name = ? WHERE part_id = ?", (dict["name"], id))
            if dict["type"] != part[2]:
                await conn.execute("UPDATE parts SET part_type = ? WHERE part_id = ?", (dict["type"].lower(), id))
            if dict["id"] != id:
                dict["id"] = id
            await conn.execute("UPDATE parts SET part_data = ? WHERE part_id = ?", (str(dict), id))
            await conn.commit()


    async def delete_part(self, id):
        async with aiosqlite.connect(self.db) as conn:
            await conn.execute("DELETE FROM parts WHERE part_id = ?", (id,))
            await conn.commit()


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
            await conn.commit()
        return pairs


    async def fetch_part(self, id):
        async with aiosqlite.connect(self.db) as conn:
            cursor = await conn.execute("SELECT * FROM parts WHERE part_id = ?", (id,))
            part = await cursor.fetchone()
            await conn.commit()
        if part is None:
            return None
        return json.loads(part[3])