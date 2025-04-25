import discord
from discord import app_commands
from discord.ext import commands
from base_cog import BaseCog

# 👇 Replace with your development guild/server ID
DEV_GUILD_ID = 1364844968375619604

class TutorialCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)
        self.userdata = db["userdata"]

    @commands.hybrid_command(
        name="tutorial",
        aliases=["tut"],
        description="View the Legion tutorial steps"
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    async def tutorial(self, ctx):
        try:
            user_id = str(ctx.author.id)

            # Fetch user data
            user_data = self.userdata.find_one({"userid": user_id})

            # Check if tutorial is already completed
            if user_data and user_data.get("tutorial", 0) != 0:
                msg = "You have already finished your tutorial. Use `/help` command for more info."
                if ctx.interaction:
                    await ctx.send(msg, ephemeral=True)
                else:
                    await ctx.send(msg)
                return

            # Create the tutorial embed
            embed = discord.Embed(
                title="Legion Tutorial",
                description=(
                    "• Start Your Legion\n"
                    "• Choose a Faction\n"
                    "• Build Basic Buildings\n"
                    "  Oil Refinery\n"
                    "  Steel Foundry\n"
                    "  Grain Silos\n"
                    "  Armory\n"
                    "  Research Lab\n"
                    "• Check for Timedown of Constructions\n"
                    "• Start the work in those Buildings\n"
                    "• Collect the outcome from those Buildings\n"
                    "• Check your Profile\n"
                    "• Check For Quests page"
                ),
                color=0x00aaff
            )

            embed.set_footer(text="Made by Alphayg")

            if ctx.interaction:
                await ctx.send(embed=embed, ephemeral=True)
            else:
                await ctx.send(embed=embed)

        except Exception as e:
            self.logger.error(f"Error in /tutorial: {e}", exc_info=True)
            try:
                if ctx.interaction:
                    await ctx.send("An error occurred. Try again later.", ephemeral=True)
                else:
                    await ctx.send("An error occurred. Try again later.")
            except:
                pass

# 🔁 This gets called automatically when the cog is loaded
async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(TutorialCommand(bot, db))
