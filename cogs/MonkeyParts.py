import discord
from discord.ext import commands
import utils
import asyncio
import re
import aiosqlite
import random
import string

green = discord.Colour(0x1e807c)
grey = discord.Colour(0x808080)

image_url_regex = re.compile(r"(http|https)://.+\.(?:png|jpg|jpeg|webp)")

valid_part_types = (
    "CPU", "GPU", "PSU", "Case", "RAM", "Motherboard", "Laptop", "Storage", "Cooler", "Fan", "Paste", "Mouse",
    "Keyboard", "Headphones", "Microphone", "Display", "WiFi")
valid_part_types_lower = [t.lower() for t in valid_part_types]


def is_submission_channel():
    def predicate(ctx):
        part_submissions_category = ctx.guild.get_channel(810298926678540329)
        return ctx.channel in part_submissions_category.text_channels

    return commands.check(predicate)


class MonkeyPart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(description="MonkeyParts related commands.", aliases=["mp"], invoke_without_command=True,
                    case_insensitive=True)
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.member)
    async def monkeyparts(self, ctx):
        info = discord.Embed(
            title="Keywords",
            description="`stop` - stop the submitting process. If you have entered at least one specification, it will "
                        "submit the data.\n"
                        "`skip` - skip the current question - only works for recommended and optional questions.\n"
                        "`cancel` - after submitting, you have 60 seconds to say \"cancel\". That will cancel "
                        "your submission.\n"
                        "`send` - after submitting, you can say \"send\" to send the submission (it will "
                        "automatically be sent after 60 seconds).",
            colour=green)
        await ctx.send(embed=info)

    # TODO: Make the verification queue resume if the bot restarts
    # TODO: Make the submission process resume if the bot restarts

    @is_submission_channel()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    @monkeyparts.command(description="Submit specifications for a part.")
    async def submit(self, ctx, *, part):
        if ctx.author.id == 790374236946432071:
            return

        part_submissions_category = ctx.guild.get_channel(810298926678540329)
        verification_queue = ctx.guild.get_channel(811625549062733845)
        moderator_role = ctx.guild.get_role(810130497485275166)
        specs = {}
        part_data = {}
        stop_message = discord.Embed(description="Stopping...", colour=green)
        chars = string.ascii_letters + string.digits

        def message_check(m):
            return m.channel == ctx.channel and m.author.id == ctx.author.id

        def cancel_message_check(m):
            return m.channel == ctx.channel and m.author.id == ctx.author.id and any(word in m.content for word in ("cancel", "send"))

        db = utils.Database(self.bot.db_path)
        results = await db.search_parts(name=part)

        # Check if there are any duplicates
        for result in results:
            if part.lower() == result[0].lower():
                duplicate = discord.Embed(description="That part already exists.", colour=green)
                await ctx.send(embed=duplicate)
                return

        required_information = {
            "type": ("Required", valid_part_types),
            "manufacturer": ("Required",),
            "sources": ("Recommended", "separate each item by a comma: `,`"),
            "images": ("Optional", "separate each URL by a comma: `,`"),
            "notes": ("Optional", "separate each item by a comma: `,`"),
        }

        # Ask for data about the part
        for item, item_info in required_information.items():
            question = f"Send the part {item} in chat:"

            if len(item_info) > 1 and isinstance(item_info[1], str):
                question = f"Specify the part {item} ({item_info[1]}) in chat:"

            question_embed = discord.Embed(description=question, colour=green)
            question_embed.set_footer(text=item_info[0])
            question_message = await ctx.send(embed=question_embed)

            response = await self.bot.wait_for("message", check=message_check, timeout=60)

            # Stop the data input if the user sends "stop"
            if "stop" in response.content.lower():
                question_embed.colour = grey
                await question_message.edit(embed=question_embed)
                await ctx.send(embed=stop_message)

                return

            # Skip the question if it's optional and the user sends "skip"
            if item_info[0] in ("Recommended", "Optional") and "skip" in response.content.lower():
                question_embed.colour = grey
                await question_message.edit(embed=question_embed)

                continue

            # Check if the user sent an image URL
            if item == "images":
                match = re.search(image_url_regex, response.content)
                skip = False

                while not match and skip is False:
                    question_embed.colour = grey
                    await question_message.edit(embed=question_embed)

                    invalid_image_url_embed = discord.Embed(
                        description="The image URL(s) you entered are invalid. Try again:",
                        colour=green)
                    invalid_image_url_message = await ctx.send(embed=invalid_image_url_embed)

                    response = await self.bot.wait_for("message", check=message_check, timeout=60)

                    if "stop" in response.content.lower():
                        invalid_image_url_embed.colour = grey
                        await invalid_image_url_message.edit(embed=invalid_image_url_embed)

                        await ctx.send(embed=stop_message)
                        return

                    if "skip" in response.content.lower():
                        invalid_image_url_embed.colour = grey
                        await invalid_image_url_message.edit(embed=invalid_image_url_embed)

                        skip = True
                        break

                    match = re.search(image_url_regex, response.content)

                    invalid_image_url_embed.colour = grey
                    await invalid_image_url_message.edit(embed=invalid_image_url_embed)

            # Check if the item is type and if the type is valid
            if len(item_info) > 1 and isinstance(item_info[1], tuple):
                while not response.content.lower() in valid_part_types_lower:
                    if "stop" in response.content.lower():
                        question_embed.colour = grey
                        await question_message.edit(embed=question_embed)
                        await ctx.send(embed=stop_message)

                        return

                    invalid_part_type = discord.Embed(
                        description=f"The type you entered is invalid. You must pick from: `{', '.join(valid_part_types)}.`",
                        colour=green
                    )
                    await ctx.send(embed=invalid_part_type)
                    response = await self.bot.wait_for("message", check=message_check, timeout=60)

            part_data[item] = response.content
            question_embed.colour = grey
            await question_message.edit(embed=question_embed)

        # Ask for the part specs
        while True:
            spec_name_embed = discord.Embed(description="What is the spec called?", colour=green)
            spec_name_message = await ctx.send(embed=spec_name_embed)
            spec_name = await self.bot.wait_for("message", check=message_check, timeout=60)

            if spec_name.content.lower() in [name.lower() for name in specs.keys()]:
                duplicate_spec = discord.Embed(description="That spec already exists!", colour=green)
                await ctx.send(embed=duplicate_spec)

                spec_name_embed.colour = grey
                await spec_name_message.edit(embed=spec_name_embed)

                continue

            if "stop" in spec_name.content.lower():
                spec_name_embed.colour = grey
                await spec_name_message.edit(embed=spec_name_embed)

                if specs:
                    formatted_data = "\n".join(
                        [f"**{item_name.capitalize()}**: {item_value}" for item_name, item_value in part_data.items()])
                    formatted_specs = "\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()])

                    stop_message = discord.Embed(
                        title="Submitted part data",
                        description="If you want to cancel the submission, type \"cancel\" within 60 seconds (in 60s "
                                    "it will automatically be sent."
                                    "If you want to send the submission, type \"send\".",
                        colour=green)
                    stop_message.add_field(name="Data", value=formatted_data, inline=False)
                    stop_message.add_field(name="Specs", value=formatted_specs, inline=False)
                    stop_message.set_footer(text="Your part will be submitted.")

                await ctx.send(embed=stop_message)

                # Let the user cancel the submission within 60s
                try:
                    cancel_message = await self.bot.wait_for("message", check=cancel_message_check, timeout=60)

                    if "cancel" in cancel_message.content.lower():
                        cancelled_embed = discord.Embed(description="Your submission has been cancelled.", colour=green)
                        await ctx.send(embed=cancelled_embed)

                        return
                    elif "send" in cancel_message.content.lower():
                        sent_embed = discord.Embed(description="Your submission has been sent.", colour=green)
                        await ctx.send(embed=sent_embed)

                except asyncio.TimeoutError:
                    pass

                # Break out of the loop asking for specs
                break

            spec_name_embed.colour = grey
            await spec_name_message.edit(embed=spec_name_embed)

            spec_values_embed = discord.Embed(
                description=f"What is the value of {spec_name.content}?\n(separate each item by a comma: `,`)",
                colour=green
            )
            spec_values_message = await ctx.send(embed=spec_values_embed)
            spec_values = await self.bot.wait_for("message", check=message_check, timeout=60)

            if "stop" in spec_values.content.lower():
                spec_values_embed.colour = grey
                await spec_values_message.edit(embed=spec_values_embed)

                if specs:
                    formatted_data = "\n".join(
                        [f"**{item_name.capitalize()}**: {item_value}" for item_name, item_value in part_data.items()])
                    formatted_specs = "\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()])

                    stop_message = discord.Embed(
                        title="Submitted part data",
                        description="If you want to cancel the submission, type \"cancel\" within 60 seconds (in 60s "
                                    "it will automatically be sent."
                                    "If you want to send the submission, type \"send\".",
                        colour=green)
                    stop_message.add_field(name="Data", value=formatted_data, inline=False)
                    stop_message.add_field(name="Specs", value=formatted_specs, inline=False)
                    stop_message.set_footer(text="Your part will be submitted.")

                await ctx.send(embed=stop_message)

                # Let the user cancel the submission within 60s
                try:
                    cancel_message = await self.bot.wait_for("message", check=cancel_message_check, timeout=60)

                    if "cancel" in cancel_message.content.lower():
                        cancelled_embed = discord.Embed(description="Your submission has been cancelled.", colour=green)
                        await ctx.send(embed=cancelled_embed)

                        return
                    elif "send" in cancel_message.content.lower():
                        sent_embed = discord.Embed(description="Your submission has been sent.", colour=green)
                        await ctx.send(embed=sent_embed)
                except asyncio.TimeoutError:
                    pass

                # Break out of the loop asking for specs
                break

            spec_values_embed.colour = grey
            await spec_values_message.edit(embed=spec_values_embed)

            # If the spec contains multiple values, it will make it a list, else it won't
            if len(spec_values.content.split(",")) == 1:
                specs[spec_name.content] = spec_values.content
            else:
                specs[spec_name.content] = spec_values.content.split(",")

        # If the user didn't add any specs, it won't send the part for verification
        if not specs:
            return

        # Process part data, send it to the verification system and act accordingly
        part_data["name"] = part
        part_data["specs"] = specs

        if "images" in part_data:
            part_data["images"] = part_data["images"].split(",")
        if "sources" in part_data:
            part_data["sources"] = part_data["sources"].split(",")
        if "notes" in part_data:
            part_data["notes"] = part_data["notes"].split(",")

        part_data["contributors"] = [str(ctx.author.id)]

        verification_message_embed = discord.Embed(
            title=f"Submission: {part}",
            # description="\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()]),
            colour=green
        )

        for item, value in part_data.items():
            field_value = value

            if isinstance(value, list):
                value = [str(item) for item in value]
                field_value = f"{', '.join(value)}."

            if isinstance(value, dict):
                field_value = "\n".join(
                    [f"**{entry_name}**: {entry_value}" for entry_name, entry_value in value.items()])

            verification_message_embed.add_field(name=item.capitalize(), value=field_value, inline=False)

        # Generate the submission ID
        submission_id = "".join([random.choice(chars) for x in range(6)])

        verification_message_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        verification_message_embed.set_footer(text=submission_id)

        verification_message = await verification_queue.send(embed=verification_message_embed)

        # Add submission to db (in case the bot restarts)
        async with aiosqlite.connect(self.bot.db_path) as conn:
            await conn.execute("INSERT into submission_tracking VALUES (?, ?)", (submission_id, str(part_data)))
            await conn.commit()

        def reaction_check(r, u):
            return not u.bot and moderator_role in u.roles and r.emoji in ("✅", "❌") and r.message.id == verification_message.id

        for reaction in ("✅", "❌"):
            await verification_message.add_reaction(reaction)

        # Wait for a reaction on the submission in the verification queue
        # If no reaction is added and it times out, it will just be ignored.
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=86400)
        except asyncio.TimeoutError:
            ignored_embed = discord.Embed(description=f"Your submission for the part **{part}** has expired.",
                                          colour=green)
            await ctx.author.send(embed=ignored_embed)
            await db.add(ctx.author.id, "ignored")

            # Delete submission from database (in case the bot restarted)
            async with aiosqlite.connect(self.bot.db_path) as conn:
                await conn.execute("DELETE FROM submission_tracking WHERE submission_id = ?", (submission_id,))
                await conn.commit()

            verification_message_embed.colour = grey
            await verification_message.edit(embed=verification_message_embed)
            return

        if reaction.emoji == "✅":
            await db.add_part(part_data)

            approved_embed = discord.Embed(
                description=f"Your submission for the part **{part}** has been approved. Thank you for contributing!",
                colour=green
            )
            await ctx.author.send(embed=approved_embed)
            await db.add(ctx.author.id, "approved")

            # Delete submission from database (in case the bot restarted)
            async with aiosqlite.connect(self.bot.db_path) as conn:
                await conn.execute("DELETE FROM submission_tracking WHERE submission_id = ?", (submission_id,))
                await conn.commit()

            verification_message_embed.colour = grey
            await verification_message.edit(embed=verification_message_embed)
        elif reaction.emoji == "❌":
            declined_embed = discord.Embed(
                description=f"Your submission for the part **{part}** has been declined.", colour=green
            )
            await ctx.author.send(embed=declined_embed)
            await db.add(ctx.author.id, "declined")

            # Delete submission from database (in case the bot restarted)
            async with aiosqlite.connect(self.bot.db_path) as conn:
                await conn.execute("DELETE FROM submission_tracking WHERE submission_id = ?", (submission_id,))
                await conn.commit()

            verification_message_embed.colour = grey
            await verification_message.edit(embed=verification_message_embed)


def setup(bot):
    bot.add_cog(MonkeyPart(bot))
