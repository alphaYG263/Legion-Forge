import discord
from discord import app_commands
from base_cog import BaseCog
import time

class PingCommand(BaseCog):
    def __init__(self, bot, db):
        super().__init__(bot, db)

    @app_commands.command(name="ping", description="Check the bot's response time")
    @app_commands.checks.cooldown(1, 5)  # Use app_commands.checks instead of commands.cooldown
    async def ping(self, interaction: discord.Interaction):
        try:
            # Record the start time
            start_time = time.time()
            
            # Defer the response to avoid timeouts
            await interaction.response.defer()
            
            # Calculate how long it took for the API response
            api_response_time = round((time.time() - start_time) * 1000)
            
            # Get bot latency (WebSocket heartbeat)
            ws_latency = round(self.bot.latency * 1000)
            
            # Create an embed with the ping information
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"API Response: `{api_response_time}ms`\nWebSocket: `{ws_latency}ms`",
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed)
            self.logger.info(f"Ping command used by {interaction.user.name} - API: {api_response_time}ms, WebSocket: {ws_latency}ms")
            
        except Exception as e:
            self.logger.error(f"Error in ping command: {str(e)}", exc_info=True)
            await interaction.followup.send("An error occurred while measuring ping.", ephemeral=True)

    # Error handler for cooldown
    @ping.error
    async def ping_error(self, interaction, error):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(
                f"Please wait {round(error.retry_after, 1)} seconds before using this command again.", 
                ephemeral=True
            )
        else:
            self.logger.error(f"Unhandled error in ping command: {error}", exc_info=True)

async def setup(bot):
    db = getattr(bot, "db", None)
    await bot.add_cog(PingCommand(bot, db))
