import discord
from discord.ext import commands
import utils

green = discord.Colour(0x1e807c)
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

    # TODO: Track user statistics

    @commands.group(description="MonkeyParts related commands.", aliases=["mp"], invoke_without_command=True,
                    case_insensitive=True)
    async def monkeyparts(self, ctx,):
        pass

    @is_submission_channel()
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.member)
    @monkeyparts.command(description="Submit specifications for a part.")
    async def submit(self, ctx, *, part):
        if ctx.author.id == 790374236946432071:
            return

        part_submissions_category = ctx.guild.get_channel(810298926678540329)
        verification_queue = ctx.guild.get_channel(810298741911060492)
        moderator_role = ctx.guild.get_role(810130497485275166)
        specs = {}
        part_data = {}
        stop_message = discord.Embed(description="Stopping...", colour=green)

        def message_check(m):
            return m.channel == ctx.channel and m.author.id == ctx.author.id

        def reaction_check(reaction, user):
            return not user.bot and moderator_role in user.roles and reaction.emoji in ("✅", "❌")

        db = utils.Database("data.db")
        results = await db.search_parts(name=part)

        # Check if there are any duplicates
        for result in results:
            if part.lower() == result[0].lower():
                # TODO: Ask user if they want to edit it instead
                duplicate = discord.Embed(description="That part already exists.", colour=green)
                await ctx.send(embed=duplicate)
                return

        required_information = {
            "type": ("Required", valid_part_types),
            "manufacturer": ("Required",),
            "sources": ("Recommended",),
            "images": ("Optional", "URLs separated by a comma and space: `, `"),
            "notes": ("Optional",),
        }

        for item, item_info in required_information.items():
            question = f"Please specify the part {item}:"

            if len(item_info) > 1 and isinstance(item_info[1], str):
                question = f"Please specify the part {item} *({item_info[1]})*:"

            item_embed = discord.Embed(description=question, colour=green)
            item_embed.set_footer(text=item_info[0])
            await ctx.send(embed=item_embed)

            response = await self.bot.wait_for("message", check=message_check, timeout=60)

            if len(item_info) > 1 and isinstance(item_info[1], tuple):
                while not response.content.lower() in valid_part_types_lower:
                    if "stop" in response.content.lower():
                        await ctx.send(embed=stop_message)
                        return

                    await ctx.send(f"The type you entered is invalid. You must pick from: `{', '.join(valid_part_types)}.`")
                    response = await self.bot.wait_for("message", check=message_check, timeout=60)

            if "stop" in response.content.lower():
                await ctx.send(embed=stop_message)
                return

            if item_info[0] in ("Recommended", "Optional") and "skip" in response.content.lower():
                continue

            part_data[item] = response.content

        # Receive the part specs
        while True:
            spec_name_embed = discord.Embed(description="What is the spec called?", colour=green)
            await ctx.send(mbed=spec_name_embed)
            spec_name = await self.bot.wait_for("message", check=message_check, timeout=60)

            if spec_name.content.lower() in [name.lower() for name in specs.keys()]:
                duplicate_spec = discord.Embed(description="That spec already exists!", colour=green)
                await ctx.send(embed=duplicate_spec)
                continue

            if "stop" in spec_name.content.lower():
                if specs:
                    formatted_specs = "\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()])
                    stop_message = discord.Embed(title="Finished spec sheet", description=formatted_specs, colour=green)
                    stop_message.set_footer(text="Your part has been submitted.")

                await ctx.send(embed=stop_message)
                break

            spec_values_embed = discord.Embed(description=f"What is the value of {spec_name.content}? (Separate each item with a comma and a space: \", \")")
            await ctx.send(embed=spec_values_embed)
            spec_values = await self.bot.wait_for("message", check=message_check, timeout=60)

            if "stop" in spec_values.content.lower():
                if specs:
                    formatted_specs = "\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()])
                    stop_message = discord.Embed(title="Finished spec sheet", description=formatted_specs, colour=green)
                    stop_message.set_footer(text="Your part has been submitted.")

                await ctx.send(embed=stop_message)
                break

            specs[spec_name.content] = spec_values.content

        if not specs:
            return

        # Process part data, send it to the verification system and act accordingly
        part_data["name"] = part
        part_data["specs"] = specs

        if "images" in part_data:
            part_data["images"] = [part_data["images"].split(", ")]
        if "sources" in part_data:
            part_data["sources"] = [part_data["sources"]]
        if "notes" in part_data:
            part_data["notes"] = [part_data["notes"]]

        part_data["contributors"] = [ctx.author.id]

        embed = discord.Embed(title=part,
                              description="\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()]),
                              colour=green)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=[t for t in valid_part_types if t.lower() == part_data["type"].lower()][0])

        verification_message = await verification_queue.send(embed=embed)
        for reaction in ("✅", "❌"):
            await verification_message.add_reaction(reaction)

        reaction, user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=86400)

        if reaction.emoji == "✅":
            await db.add_part(part_data)
            # TODO: Let the user know it was accepted
        elif reaction.emoji == "❌":
            # TODO: Let the user know the part was denied
            pass


def setup(bot):
    bot.add_cog(MonkeyPart(bot))
