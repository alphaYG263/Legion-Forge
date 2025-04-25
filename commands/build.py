import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timedelta
from base_cog import BaseCog

# 👇 Replace with your development guild/server ID if needed
DEV_GUILD_ID = 1364844968375619604

class BuildCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)
        self.userdata = db["userdata"]
        self.invdata = db["invdata"]
        
        # Load buildings from file
        try:
            with open(os.path.join("data", "buildings.json"), "r") as f:
                self.buildings = json.load(f)
                self.building_keys = list(self.buildings.keys())
        except Exception as e:
            self.logger.error(f"Error loading buildings: {e}")
            self.buildings = {}
            self.building_keys = []
        
        # Load emojis from file
        try:
            with open(os.path.join("data", "emojis.json"), "r") as f:
                self.emojis = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading emojis: {e}")
            self.emojis = {}
        
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
    
    # Create embed for building display
    def create_building_embed(self, page_num, user_data):
        if not self.building_keys or page_num >= len(self.building_keys):
            return discord.Embed(title="No buildings available", color=0xff0000)
        
        building_name = self.building_keys[page_num]
        building_data = self.buildings[building_name]
        
        embed = discord.Embed(
            title=f"Building: {building_name}",
            description=building_data.get("description", "No description available."),
            color=0x00aaff
        )
        
        # Add requirements as fields
        for req_name, req_value in building_data.items():
            if req_name != "description" and req_name != "id":
                emoji = self.emojis.get(req_name.lower(), "")
                
                # Check if user meets requirement
                user_value = user_data.get(req_name.lower(), 0)
                sufficient = user_value >= req_value
                
                # Format the field to show if requirement is met
                status = "✅" if sufficient else "❌"
                embed.add_field(
                    name=f"{req_name.capitalize()} {emoji}",
                    value=f"{req_value}  {status}",
                    inline=True
                )
        
        embed.set_footer(text=f"Building {page_num+1}/{len(self.building_keys)}")
        return embed
    
    # Check if user meets all requirements
    def meets_requirements(self, user_data, building_name):
        building_data = self.buildings.get(building_name, {})
        for req_name, req_value in building_data.items():
            if req_name != "description" and req_name != "id":
                user_value = user_data.get(req_name.lower(), 0)
                if user_value < req_value:
                    return False
        return True
    
    @commands.hybrid_command(
        name="build",
        description="Build structures for your Legion"
    )
    @app_commands.guilds(discord.Object(id=DEV_GUILD_ID))  # For faster slash command registration
    async def build(self, ctx):
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
                    await ctx.send("Please form a Legion by using the `/start` command first!", ephemeral=True)
                else:  # Prefix command
                    await ctx.send("Please form a Legion by using the `/start` command first!")
                return
            
            # Check if buildings data loaded properly
            if not self.building_keys:
                if ctx.interaction:
                    await ctx.send("Building data unavailable. Please try again later.", ephemeral=True)
                else:
                    await ctx.send("Building data unavailable. Please try again later.")
                return
            
            # Get inventory data
            inv_data = self.invdata.find_one({"userid": user_id})
            if not inv_data:
                inv_data = {"userid": user_id, "buildings": []}
                self.invdata.insert_one(inv_data)
            
            # Create buttons for pagination and construction
            class BuildingView(discord.ui.View):
                def __init__(self, parent, user_data, inv_data, author_id):
                    super().__init__(timeout=60)  # 1 minute timeout
                    self.parent = parent
                    self.page = 0
                    self.user_data = user_data
                    self.inv_data = inv_data
                    self.author_id = author_id
                    self.update_buttons()
                
                def update_buttons(self):
                    # Update button states based on current page
                    self.left_button.disabled = self.page <= 0
                    self.right_button.disabled = self.page + 1 >= len(self.parent.building_keys) or self.page >= 12
                
                async def on_timeout(self):
                    # Disable all buttons and show timeout message
                    for child in self.children:
                        child.disabled = True
                    
                    embed = self.message.embeds[0]
                    embed.description += "\n\n**Interaction timed out.**"
                    await self.message.edit(embed=embed, view=self)
                
                # Author-only check for all buttons
                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    if interaction.user.id != self.author_id:
                        await interaction.response.send_message("You can't use these buttons!", ephemeral=True)
                        return False
                    return True
                
                @discord.ui.button(label="◀️", style=discord.ButtonStyle.green)
                async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.page > 0:
                        self.page -= 1
                        self.update_buttons()
                        embed = self.parent.create_building_embed(self.page, self.user_data)
                        await interaction.response.edit_message(embed=embed, view=self)
                    else:
                        await interaction.response.defer()
                
                @discord.ui.button(label="Construct", style=discord.ButtonStyle.red)
                async def construct_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    current_building = self.parent.building_keys[self.page]
                    building_id = self.parent.buildings[current_building].get("id", 0)
                    
                    # Check if user already has this building
                    user_buildings = self.inv_data.get("buildings", [])
                    if any(b.get("id") == building_id for b in user_buildings):
                        await interaction.response.send_message(
                            f"You already constructed {current_building}!",
                            ephemeral=True
                        )
                        return
                    
                    # Check if user meets requirements
                    if not self.parent.meets_requirements(self.user_data, current_building):
                        await interaction.response.send_message(
                            "You don't meet the requirements to build this!",
                            ephemeral=True
                        )
                        return
                    
                    # Create confirmation view
                    confirm_view = ConfirmView(self.parent, current_building, building_id, self.user_data, self.inv_data, self.author_id)
                    confirm_embed = discord.Embed(
                        title="Confirm Construction",
                        description=f"Are you sure you want to construct **{current_building}**?",
                        color=0xffaa00
                    )
                    
                    await interaction.response.send_message(embed=confirm_embed, view=confirm_view)
                    confirm_view.message = await interaction.original_response()
                
                @discord.ui.button(label="▶️", style=discord.ButtonStyle.green)
                async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.page + 1 < len(self.parent.building_keys) and self.page < 12:
                        self.page += 1
                        self.update_buttons()
                        embed = self.parent.create_building_embed(self.page, self.user_data)
                        await interaction.response.edit_message(embed=embed, view=self)
                    else:
                        await interaction.response.defer()
            
            # Create confirmation view for construction
            class ConfirmView(discord.ui.View):
                def __init__(self, parent, building_name, building_id, user_data, inv_data, author_id):
                    super().__init__(timeout=10)  # 10 seconds timeout
                    self.parent = parent
                    self.building_name = building_name
                    self.building_id = building_id
                    self.user_data = user_data
                    self.inv_data = inv_data
                    self.author_id = author_id
                
                async def on_timeout(self):
                    # Disable all buttons and show timeout message
                    for child in self.children:
                        child.disabled = True
                    
                    embed = self.message.embeds[0]
                    embed.description += "\n\n**Interaction timed out.**"
                    await self.message.edit(embed=embed, view=self)
                
                # Author-only check for all buttons
                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    if interaction.user.id != self.author_id:
                        await interaction.response.send_message("You can't use these buttons!", ephemeral=True)
                        return False
                    return True
                
                @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
                async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Subtract resources
                    building_data = self.parent.buildings[self.building_name]
                    updates = {}
                    
                    for req_name, req_value in building_data.items():
                        if req_name != "description" and req_name != "id":
                            updates[req_name.lower()] = -req_value
                    
                    # Update user's resources
                    for resource, amount in updates.items():
                        self.parent.userdata.update_one(
                            {"userid": str(interaction.user.id)},
                            {"$inc": {resource: amount}}
                        )
                    
                    # Add building to inventory
                    self.parent.invdata.update_one(
                        {"userid": str(interaction.user.id)},
                        {"$push": {"buildings": {"id": self.building_id, "name": self.building_name}}}
                    )
                    
                    # Update message
                    for child in self.children:
                        child.disabled = True
                    
                    success_embed = discord.Embed(
                        title="Construction Complete",
                        description=f"Successfully constructed **{self.building_name}**!",
                        color=0x00ff00
                    )
                    
                    await interaction.response.edit_message(embed=success_embed, view=self)
                
                @discord.ui.button(label="No", style=discord.ButtonStyle.red)
                async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Disable buttons and show cancellation message
                    for child in self.children:
                        child.disabled = True
                    
                    cancel_embed = discord.Embed(
                        title="Construction Cancelled",
                        description="Interaction cancelled.",
                        color=0xff0000
                    )
                    
                    await interaction.response.edit_message(embed=cancel_embed, view=self)
            
            # Create initial building embed and view
            embed = self.create_building_embed(0, user_data)
            view = BuildingView(self, user_data, inv_data, ctx.author.id)
            
            # Send the embed with buttons
            if ctx.interaction:  # Slash command
                await ctx.defer(ephemeral=False)
                message = await ctx.send(embed=embed, view=view)
            else:  # Prefix command
                message = await ctx.send(embed=embed, view=view)
            
            # Store the message for view callbacks
            view.message = message
            
        except Exception as e:
            self.logger.error(f"Error in /build: {e}", exc_info=True)
            
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
    await bot.add_cog(BuildCommand(bot, db))
