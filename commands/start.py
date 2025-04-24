import discord
from discord import app_commands
import time
from pymongo import MongoClient
from base_cog import BaseCog

# 👇 Replace with your development guild/server ID
DEV_GUILD_ID = 1364844968375619604

class StartCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)
        self.userdata = db["userdata"]
        self.invdata = db["invdata"]
        self.globaldata = db["globaldata"]

    # 🔐 Guild-only command: fast registration, useful for dev/testing
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))
    @app_commands.command(name="start", description="Forge your Legion!")
    async def start(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)

            # Exit early if user already exists
            if self.userdata.find_one({"userid": user_id}):
                await interaction.response.send_message("You already forged a Legion!", ephemeral=True)
                return

            await interaction.response.defer(thinking=True)  # Avoids timeouts

            user_data = {
                "userid": user_id,
                "exp": 0,
                "premium": int(time.time() + 3600),
                "food": 100,
                "gold": 1000,
                "faction": "",
                "ext1": 0, "ext2": 0, "ext3": 0, "ext4": 0, "ext5": 0,
                "ext6": "", "ext7": "", "ext8": "", "ext9": "", "ext10": ""
            }

            inv_data = {
                "userid": user_id,
                "units": [],
                "ext1": [], "ext2": [], "ext3": [], "ext4": [], "ext5": []
            }

            self.userdata.insert_one(user_data)
            self.invdata.insert_one(inv_data)
            self.globaldata.update_one({"owner": "alphayg"}, {"$inc": {"users": 1}})

            embed = discord.Embed(
                title="Legion Forge",
                description=f"Welcome Supreme Leader {interaction.user.display_name}, prepare your Legion...",
                color=0x00ff00
            )

            await interaction.followup.send(embed=embed)
            self.logger.info(f"New user joined: {interaction.user.display_name} ({user_id})")

        except Exception as e:
            self.logger.error(f"Error in /start: {e}", exc_info=True)
            await interaction.followup.send("An error occurred. Try again later.", ephemeral=True)


# 🔁 This gets called automatically when the cog is loaded
async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(StartCommand(bot, db))
