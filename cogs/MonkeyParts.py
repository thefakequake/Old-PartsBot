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

    # TODO: Make the command a group

    @is_submission_channel()
    @commands.cooldown(rate=1, per=1, type=commands.BucketType.member)
    @commands.command(description="Submit specifications for a part.")
    async def submitpart(self, ctx, *, part):
        part_submissions_category = ctx.guild.get_channel(810298926678540329)
        verification_queue = ctx.guild.get_channel(810298741911060492)
        moderator_role = ctx.guild.get_role(810130497485275166)
        specs = {}
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
                duplicate = discord.Embed(description="Part already exists.", colour=green)
                await ctx.send(embed=duplicate)
                return

        # Ask for the part type
        part_type_embed = discord.Embed(description="What type is this part?", colour=green)
        part_type_embed.set_footer(text="Required")
        await ctx.send(embed=part_type_embed)
        part_type = await self.bot.wait_for("message", check=message_check, timeout=60)

        while not part_type.content.lower() in valid_part_types_lower:
            if "stop" in part_type.content.lower():
                await ctx.send(embed=stop_message)
                return

            await ctx.send(
                f"The type you entered is invalid. You must pick from: `{', '.join(valid_part_types)}.`")
            part_type = await self.bot.wait_for("message", check=message_check, timeout=60)

        # Ask for the manufacturer
        manufacturer_embed = discord.Embed(description="What is the manufacturer for this part?", colour=green)
        manufacturer_embed.set_footer(text="Required")
        await ctx.send(embed=manufacturer_embed)
        manufacturer = await self.bot.wait_for("message", check=message_check, timeout=60)
        if "stop" in manufacturer.content.lower():
            await ctx.send(embed=stop_message)
            return

        # Ask for sources TODO: Make the sources optional
        sources_embed = discord.Embed(description="What are the sources for the specs?", colour=green)
        sources_embed.set_footer(text="Recommended")
        await ctx.send(embed=sources_embed)
        sources = await self.bot.wait_for("message", check=message_check, timeout=60)
        if "stop" in sources.content.lower():
            await ctx.send(embed=stop_message)
            return

        # Ask for part images TODO: Make the images optional
        images_embed = discord.Embed(description="What image URLs are there for the part?\n*(Separated by a comma and "
                                                 "space: `, `)*", colour=green)
        images_embed.set_footer(text="Optional")
        await ctx.send(embed=images_embed)
        image_urls = await self.bot.wait_for("message", check=message_check, timeout=60)
        if "stop" in image_urls.content.lower():
            await ctx.send(embed=stop_message)
            return

        # Ask for notes on the part TODO: Make the notes optional
        notes_embed = discord.Embed(description="Are there any notes on the product?", colour=green)
        notes_embed.set_footer(text="Optional")
        await ctx.send(embed=notes_embed)
        notes = await self.bot.wait_for("message", check=message_check, timeout=60)
        if "stop" in notes.content.lower():
            await ctx.send(embed=stop_message)
            return

        images = image_urls.content.split(", ")

        # Receive the part specs
        while True:
            await ctx.send("What is the spec called?")
            spec_name = await self.bot.wait_for("message", check=message_check, timeout=60)

            if spec_name.content.lower() in [name.lower() for name in specs.keys()]:
                await ctx.send("That spec already exists!")
                continue

            if "stop" in spec_name.content.lower():
                if specs:
                    formatted_specs = "\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()])
                    stop_message = discord.Embed(title="Finished spec sheet", description=formatted_specs, colour=green)
                    stop_message.set_footer(text="Your part has been submitted.")

                await ctx.send(embed=stop_message)
                break

            await ctx.send(
                f"What is the value of {spec_name.content}? (Separate each item with a comma and a space: \", \")")
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
        part_data = {
            "name": part,
            "type": part_type.content,
            "manufacturer": manufacturer.content,
            "specs": specs,
            "sources": sources.content,
            "images": images,
            "notes": notes.content,
            "contributors": str(ctx.author.id)
        }

        embed = discord.Embed(title=part,
                              description="\n".join([f"**{s_name}:** {s_value}" for s_name, s_value in specs.items()]),
                              colour=green)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=[t for t in valid_part_types if t.lower() == part_type.content.lower()][0])

        verification_message = await verification_queue.send(embed=embed)
        for reaction in ("✅", "❌"):
            await verification_message.add_reaction(reaction)

        reaction, user = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=None)

        if reaction.emoji == "✅":
            await db.add_part(part_data)
            # TODO: Let the user know it was accepted
        elif reaction.emoji == "❌":
            # TODO: Let the user know the part was denied
            pass


def setup(bot):
    bot.add_cog(MonkeyPart(bot))
