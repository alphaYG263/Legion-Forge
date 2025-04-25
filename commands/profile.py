import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from base_cog import BaseCog

# 👇 Replace with your development guild/server ID if needed
DEV_GUILD_ID = 1364844968375619604

class ProfileCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)
        self.userdata = db["userdata"]
        
        # Load emojis from file
        try:
            with open(os.path.join("data", "emojis.json"), "r") as f:
                self.emojis = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading emojis: {e}")
            self.emojis = {
                "experience": "✨",
                "gold": "💰",
                "steel": "⚙️",
                "oil": "🛢️",
                "food": "🍗",
                "intel": "🔍"
            }
        
        # Cooldown tracking
        self.cooldowns = {}
    
    # Custom cooldown check
    async def is_on_cooldown(self, user_id):
        if user_id in self.cooldowns:
            current_time = datetime.now()
            if current_time < self.cooldowns[user_id]:
                # Calculate remaining time in seconds
                remaining = (self.cooldowns[user_id] - current_time).total_seconds()
                return True, int(remaining)
        
        # Set cooldown for 15 seconds
        self.cooldowns[user_id] = datetime.now() + timedelta(seconds=15)
        return False, 0
    
    @commands.hybrid_command(
        name="profile", 
        aliases=["pr"],  # Alias only works for prefix commands
        description="View your Legion profile"
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))  # For faster slash command registration
    async def profile(self, ctx):
        try:
            user_id = str(ctx.author.id)
            
            # Check for cooldown
            on_cooldown, remaining = await self.is_on_cooldown(user_id)
            if on_cooldown:
                if ctx.interaction:  # Slash command
                    await ctx.send(f"You need to wait {remaining}s to use it again.", ephemeral=True)
                else:  # Prefix command
                    await ctx.send(f"You need to wait {remaining}s to use it again.")
                return
            
            # First check: See if user exists in database
            user_data = self.userdata.find_one({"userid": user_id})
            if not user_data:
                if ctx.interaction:  # Slash command
                    await ctx.send("Please begin your Legion by using the `/start` command first!", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("Please begin your Legion by using the `/start` command first!")
                return
            
            # Second check: See if user completed tutorial
            if user_data.get("tutorial", 0) == 0:
                if ctx.interaction:  # Slash command  
                    await ctx.send("Please finish your tutorial commands first!", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("Please finish your tutorial commands first!")
                return
            
            # Calculate premium status
            premium_status = True if user_data.get("premium", 0) == 1 else False
            
            # Create the profile embed
            # Determine embed color based on premium status
            embed_color = 0xffd700 if premium_status else 0x00aaff  # Gold if premium, blue otherwise

            # Create the profile embed
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s Legion Profile",
                color=embed_color
            )
            
            # Set the user's avatar as the thumbnail
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            # Add profile details to the description
            description = (
                f"**Faction**: `{user_data.get('faction', 'None')}`\n"
                f"**Premium User**: `{premium_status}`\n"
            )

            embed.description = description

            embed.add_field(
                name="Exp",
                value=f"`{user_data.get('exp', 0)}` {self.emojis.get('experience', '✨')}",
                inline=True
            )
            embed.add_field(
                name="Gold",
                value=f"`{user_data.get('gold', 0)}` {self.emojis.get('gold', '💰')}",
                inline=True
            )
            embed.add_field(
                name="Intel",
                value=f"`{user_data.get('intel', 0)}` {self.emojis.get('intel', '🔍')}",
                inline=True
            )
            embed.add_field(
                name="Oil",
                value=f"`{user_data.get('oil', 0)}` {self.emojis.get('oil', '🛢️')}",
                inline=True
            )
            embed.add_field(
                name="Steel",
                value=f"`{user_data.get('steel', 0)}` {self.emojis.get('steel', '⚙️')}",
                inline=True
            )
            embed.add_field(
                name="Food",
                value=f"`{user_data.get('food', 0)}` {self.emojis.get('food', '🍗')}",
                inline=True
            )
            
            # Add footer
            embed.set_footer(text="Made by Alphayg")
            
            # Send the embed
            if ctx.interaction:  # Slash command
                await ctx.send(embed=embed)
            else:  # Prefix command
                await ctx.send(embed=embed)
            
        except Exception as e:
            self.logger.error(f"Error in /profile: {e}", exc_info=True)
            
            try:
                if ctx.interaction:  # Slash command
                    await ctx.send("An error occurred. Try again later.", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("An error occurred. Try again later.")
            except:
                pass

# 🔁 This gets called automatically when the cog is loaded
async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(ProfileCommand(bot, db))
