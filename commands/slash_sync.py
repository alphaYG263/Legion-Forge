import discord
from discord.ext import commands
from discord import app_commands

class SlashSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sync", description="Sync slash commands with Discord")
    @app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            if interaction.guild:
                # Sync only to current guild
                await self.bot.tree.sync(guild=interaction.guild)
                await interaction.followup.send(
                    f"✅ Synced slash commands to this guild: `{interaction.guild.name}`", ephemeral=True
                )
            else:
                # Global sync (slower, ratelimited)
                await self.bot.tree.sync()
                await interaction.followup.send("✅ Globally synced slash commands.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: `{e}`", ephemeral=True)

    @app_commands.command(name="clear_sync", description="Clear and re-sync slash commands")
    @app_commands.default_permissions(administrator=True)
    async def clear_sync_commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            if interaction.guild:
                await self.bot.tree.clear_commands(guild=interaction.guild)
                await self.bot.tree.sync(guild=interaction.guild)
                await interaction.followup.send("🧼 Cleared & re-synced this guild's slash commands.", ephemeral=True)
            else:
                await self.bot.tree.clear_commands()
                await self.bot.tree.sync()
                await interaction.followup.send("🧼 Cleared & re-synced **global** slash commands.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Clear sync failed: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlashSync(bot))
