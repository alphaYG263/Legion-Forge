import discord
from discord.ext import commands
from discord import app_commands
from base_cog import BaseCog

class SlashSync(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)

    @app_commands.command(name="sync", description="Sync slash commands with Discord")
    @app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            if interaction.guild:
                # Sync only to current guild
                synced = await self.bot.tree.sync(guild=interaction.guild)
                await interaction.followup.send(
                    f"✅ Synced {len(synced)} slash commands to this guild: `{interaction.guild.name}`", ephemeral=True
                )
                self.logger.info(f"Manually synced {len(synced)} commands to guild {interaction.guild.name}")
            else:
                # Global sync (slower, ratelimited)
                synced = await self.bot.tree.sync()
                await interaction.followup.send(f"✅ Globally synced {len(synced)} slash commands.", ephemeral=True)
                self.logger.info(f"Manually synced {len(synced)} commands globally")

        except Exception as e:
            await interaction.followup.send(f"❌ Sync failed: `{e}`", ephemeral=True)
            self.logger.error(f"Sync failed: {e}", exc_info=True)

    @app_commands.command(name="clear_sync", description="Clear and re-sync slash commands")
    @app_commands.default_permissions(administrator=True)
    async def clear_sync_commands(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True, ephemeral=True)

            if interaction.guild:
                self.bot.tree.clear_commands(guild=interaction.guild)
                synced = await self.bot.tree.sync(guild=interaction.guild)
                await interaction.followup.send(f"🧼 Cleared & re-synced {len(synced)} guild slash commands.", ephemeral=True)
                self.logger.info(f"Cleared and re-synced {len(synced)} commands for guild {interaction.guild.name}")
            else:
                self.bot.tree.clear_commands()
                synced = await self.bot.tree.sync()
                await interaction.followup.send(f"🧼 Cleared & re-synced {len(synced)} global slash commands.", ephemeral=True)
                self.logger.info(f"Cleared and re-synced {len(synced)} global commands")

        except Exception as e:
            await interaction.followup.send(f"❌ Clear sync failed: `{e}`", ephemeral=True)
            self.logger.error(f"Clear sync failed: {e}", exc_info=True)

async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(SlashSync(bot, db))
