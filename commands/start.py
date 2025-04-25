import discord
from discord import app_commands
from discord.ext import commands
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
    
    # Hybrid command - works as both slash and prefix command
    @commands.hybrid_command(
        name="start", 
        description="Forge your Legion!",
        with_app_command=True
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))  # For faster slash command registration
    async def start(self, ctx):
        try:
            user_id = str(ctx.author.id)
            
            # Exit early if user already exists
            if self.userdata.find_one({"userid": user_id}):
                # Check if this is a slash command or prefix command
                if ctx.interaction:  # This checks if it's invoked as a slash command
                    await ctx.interaction.response.send_message("You already forged a Legion!", ephemeral=True)
                else:  # It's a regular prefix command
                    await ctx.send("You already forged a Legion!")
                return
            
            # Handle different contexts for defer
            if ctx.interaction:  # Slash command
                await ctx.defer()
            else:  # Prefix command
                message = await ctx.send("Registering...")
            
            user_data = {
                "userid": user_id,
                "exp": 0,
                "premium": int(time.time() + 3600),
                "oncepremium": 0,
                "battles": 0,
                "wins": 0,
                "tutorial": 0,
                "food": 100,
                "steel": 1000,
                "oil": 1000,
                "gold": 1000,
                "intel": 100,
                "faction": "",
                "ext1": 0, "ext2": 0, "ext3": 0, "ext4": 0, "ext5": 0,
                "ext6": "", "ext7": "", "ext8": "", "ext9": "", "ext10": "", "cooldowns": []
            }
            
            inv_data = {
                "userid": user_id,
                "units": [],
                "buildings": [], "timedowns": [], "ext1": [], "ext2": [], "ext3": [], "ext4": [], "ext5": []
            }
            
            self.userdata.insert_one(user_data)
            self.invdata.insert_one(inv_data)
            self.globaldata.update_one({"owner": "alphayg"}, {"$inc": {"users": 1}})
            
            embed = discord.Embed(
                title="Legion Forge",
                description=f"Welcome Supreme Leader **{ctx.author.display_name}**, prepare your Legion...\nLets get started , Choose an Faction using /choosefaction\nNova Pact - **15%** Attack Buff\nSentinel Order - **10%** Defense Buff\nCrimson Reign - **5%** Both Buff",
                color=0x00ff00
            )
            
            # Handle different contexts for sending response
            if ctx.interaction:  # Slash command
                await ctx.send(embed=embed)
            else:  # Prefix command
                await message.edit(content=None, embed=embed)
            
            # Log the new user
            user_name = ctx.author.display_name
            self.logger.info(f"New user joined: {user_name} ({user_id})")
            
        except Exception as e:
            self.logger.error(f"Error in /start: {e}", exc_info=True)
            
            # Handle error messages
            try:
                if ctx.interaction:  # Slash command
                    await ctx.send("An error occurred. Try again later.", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("An error occurred. Try again later.")
            except:
                # Fallback if the previous error handling fails
                try:
                    await ctx.send("An error occurred. Try again later.")
                except:
                    pass  # At this point, we can't do much more

# 🔁 This gets called automatically when the cog is loaded
async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(StartCommand(bot, db))
