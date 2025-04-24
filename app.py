import discord
from discord.ext import commands
import logging
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DEV_GUILD_ID = 1364844968375619604  # Your development guild ID

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Setup logging
LOGGING_CHANNEL_ID = 1364844968375619607
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

class DiscordHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.channel = None

    async def send(self, message):
        if self.channel is None:
            self.channel = self.bot.get_channel(self.channel_id)
            if self.channel is None:
                return
        await self.channel.send(message)

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.create_task(self.send(log_entry))

@bot.command(name='reload')
@commands.is_owner()
async def reload_cogs(ctx):
    for file in os.listdir('./commands'):
        if file.endswith('.py') and not file.startswith('__'):
            ext = f'commands.{file[:-3]}'
            try:
                await bot.unload_extension(ext)
                await bot.load_extension(ext)
                await ctx.send(f"🔄 Reloaded `{ext}`")
                logger.info(f"Reloaded `{ext}`")
            except Exception as e:
                await ctx.send(f"❌ Failed to reload `{ext}`")
                logger.error(f"Failed to reload {ext}: {e}")
    
    # Sync commands after reload
    try:
        dev_guild = discord.Object(id=DEV_GUILD_ID)
        synced = await bot.tree.sync(guild=dev_guild)
        await ctx.send(f"✅ Synced {len(synced)} commands to dev guild")
    except Exception as e:
        await ctx.send(f"❌ Failed to sync commands: {e}")
        logger.error(f"Failed to sync commands: {e}")

async def load_cogs():
    for file in os.listdir('./commands'):
        if file.endswith('.py') and not file.startswith('__'):
            ext = f'commands.{file[:-3]}'
            try:
                await bot.load_extension(ext)
                logger.info(f"Loaded {ext}")
            except Exception as e:
                logger.error(f"Error loading {ext}: {e}")

@bot.event
async def on_ready():
    handler = DiscordHandler(bot, LOGGING_CHANNEL_ID)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    bot.logger = logger

    print(f"{bot.user} is online!")
    logger.info(f"{bot.user} is online!")
    
    # Load all cogs first
    await load_cogs()
    
    # Then sync commands AFTER all cogs are loaded
    try:
        dev_guild = discord.Object(id=DEV_GUILD_ID)
        synced = await bot.tree.sync(guild=dev_guild)
        logger.info(f"Synced {len(synced)} commands to dev guild")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://alphayg:yogialpha12345@fantasyleague.1id3c.mongodb.net/?retryWrites=true&w=majority&appName=FantasyLeague")
bot.db = MongoClient(mongo_uri)["Forgelegion"]

bot.run(TOKEN)
