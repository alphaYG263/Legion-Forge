import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from base_cog import BaseCog

# 👇 Replace with your development guild/server ID if needed
DEV_GUILD_ID = 1364844968375619604

class ChooseFactionCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)
        self.userdata = db["userdata"]
    
    @commands.hybrid_command(
        name="choosefaction", 
        aliases=["cf"],  # Alias only works for prefix commands
        description="Choose your Legion's faction!"
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))  # For faster slash command registration
    async def choosefaction(self, ctx):
        try:
            user_id = str(ctx.author.id)
            
            # First check: See if user exists in database
            user_data = self.userdata.find_one({"userid": user_id})
            if not user_data:
                if ctx.interaction:  # Slash command
                    await ctx.send("Please begin your Legion by using the `/start` command first!", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("Please begin your Legion by using the `/start` command first!")
                return
            
            # Second check: See if user already has a faction
            if user_data.get("faction", "") != "":
                if ctx.interaction:  # Slash command  
                    await ctx.send("You have already chosen your faction!", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("You have already chosen your faction!")
                return
            
            # Create the faction selection embed
            embed = discord.Embed(
                title="Choose Your Faction",
                description="Choose from the below factions:\n\n" +
                            "Nova Pact - **15%** Attack Buff\n" +
                            "Sentinel Order - **10%** Defense Buff\n" +
                            "Crimson Reign - **5%** Both Buff",
                color=0x00ffff
            )
            
            # Create the buttons
            class FactionButtons(discord.ui.View):
                def __init__(self, parent, timeout=30):
                    super().__init__(timeout=timeout)
                    self.parent = parent
                    self.value = None
                
                async def on_timeout(self):
                    # When timeout occurs, disable all buttons
                    for child in self.children:
                        child.disabled = True
                    
                    # Update the message with disabled buttons and timeout message
                    embed.description += "\n\n**Interaction timed out.**"
                    await self.message.edit(embed=embed, view=self)
                
                @discord.ui.button(label="Nova Pact", style=discord.ButtonStyle.blurple)
                async def nova_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("You can't use this button!", ephemeral=True)
                        return
                    
                    await self.process_selection(interaction, "Nova Pact")
                
                @discord.ui.button(label="Sentinel Order", style=discord.ButtonStyle.green)
                async def sentinel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("You can't use this button!", ephemeral=True)
                        return
                    
                    await self.process_selection(interaction, "Sentinel Order")
                
                @discord.ui.button(label="Crimson Reign", style=discord.ButtonStyle.red)
                async def crimson_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("You can't use this button!", ephemeral=True)
                        return
                    
                    await self.process_selection(interaction, "Crimson Reign")
                
                async def process_selection(self, interaction, faction):
                    # Update the user's faction in the database
                    self.parent.userdata.update_one(
                        {"userid": str(interaction.user.id)},
                        {"$set": {"faction": faction}}
                    )
                    
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                    
                    # Create a new embed for the confirmation
                    success_embed = discord.Embed(
                        title="Faction Selected",
                        description=f"You have joined the **{faction}**! Let's do the next step.",
                        color=0x00ff00
                    )
                    
                    # Update the message
                    await interaction.response.edit_message(embed=success_embed, view=None)
                    self.value = faction
                    self.stop()
            
            # Send the embed with buttons
            view = FactionButtons(self)
            
            # Handle different contexts for sending
            if ctx.interaction:  # Slash command
                await ctx.defer(ephemeral=False)
                message = await ctx.send(embed=embed, view=view)
            else:  # Prefix command
                message = await ctx.send(embed=embed, view=view)
            
            # Store the message for the on_timeout handler
            view.message = message
            
            # Wait for the view to finish (button clicked or timeout)
            await view.wait()
            
            if view.value:
                self.logger.info(f"User {ctx.author.display_name} ({user_id}) chose faction: {view.value}")
        
        except Exception as e:
            self.logger.error(f"Error in /choosefaction: {e}", exc_info=True)
            
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
    await bot.add_cog(ChooseFactionCommand(bot, db))
