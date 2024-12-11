"""
Price tracking tool for Discord bot
"""

__all__ = ['PriceTrackerTool']

from agency_swarm.tools import BaseTool
from pydantic import Field
import os
from dotenv import load_dotenv
import requests
from web3 import Web3
import discord
from discord.ext import tasks
import asyncio
from typing import Optional
from pydantic import ConfigDict
import logging

load_dotenv()

# Add error checking for environment variables
guild_id = os.getenv("GUILD_ID")
if not guild_id:
    raise ValueError("GUILD_ID not found in .env file")
if guild_id == 'your_discord_server_id':
    raise ValueError("Please replace 'your_discord_server_id' in .env with your actual Discord server ID")

GUILD_ID = int(guild_id)

# Constants
PDT_CONTRACT = "0xeff2A458E464b07088bDB441C21A42AB4b61e07E"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

logger = logging.getLogger(__name__)

class PriceTrackerTool(BaseTool):
    """
    Tool for tracking PDT-Token price and updating Discord role/status
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    update_interval: int = Field(
        default=300,  # 5 minutes - production interval
        description="Interval in seconds between price updates"
    )
    
    client: Optional[str] = Field(
        default=None,
        description="Discord client instance"
    )
    
    previous_price: Optional[float] = Field(
        default=None,
        description="Previous price value"
    )
    
    is_running: bool = Field(
        default=False,
        description="Flag to track if the bot is running"
    )
    
    price_update_loop: Optional[tasks.Loop] = Field(
        default=None,
        description="Task loop for price updates"
    )

    _discord_client: Optional[discord.Client] = None
    _price_update_loop: Optional[tasks.Loop] = None
    _previous_price: Optional[float] = None
    _is_running: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        intents = discord.Intents.all()
        # Explicitly set required intents
        intents.guilds = True  # Required for guild operations
        intents.members = True  # Required for member operations
        intents.message_content = True  # Required for message content
        intents.presences = True  # Required for presence updates
        self.price_update_loop = None
        print("Initializing Discord client with intents:", intents)
        self._discord_client = discord.Client(intents=intents)
        self.setup_discord_bot()

    def create_price_loop(self):
        try:
            loop = tasks.loop(seconds=self.update_interval)(self.price_update_loop_func)
            print(f"Created price update loop with interval: {self.update_interval} seconds")
            return loop
        except Exception as e:
            print(f"Error creating price update loop: {e}")
            return None

    async def price_update_loop_func(self):
        try:
            # Fetch current price and 24h change from Coingecko
            print(f"\n[{discord.utils.utcnow()}] Running price update...")
            print("Fetching price data...")
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/token_price/base?contract_addresses=0xeff2a458e464b07088bdb441c21a42ab4b61e07e&vs_currencies=usd&include_24hr_change=true"
            , timeout=10)  # Add timeout to prevent hanging
            data = response.json()
            
            price = data[PDT_CONTRACT.lower()]['usd']
            change_24h = data[PDT_CONTRACT.lower()]['usd_24h_change']

            logger.info(f"Price data fetched: ${price:.4f} ({change_24h:+.2f}%)")
            print(f"\nPrice update: ${price:.4f} (24h change: {change_24h:+.2f}%)")
            # Update bot's own role color
            try:
                guild = self._discord_client.get_guild(GUILD_ID)
                if guild:
                    # Get bot's role
                    bot_member = guild.get_member(self._discord_client.user.id)
                    if not bot_member:
                        print("Bot member not found in guild")
                        return
                    
                    # Debug role hierarchy
                    logger.debug("\nRole hierarchy:")
                    for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
                        logger.debug(f"- {role.name} (position: {role.position})")

                    # Debug bot permissions
                    logger.debug("\nBot permissions:")
                    for perm, value in bot_member.guild_permissions:
                        if value:
                            logger.debug(f"- {perm}")

                    logger.info(f"Bot's role position: {bot_member.top_role.position}")
                    
                    # Update bot's nickname
                    await bot_member.edit(
                        nick=f"PDT ${price:.4f} {'📈' if change_24h >= 0 else '📉'}"
                    )
                    print(f"Updated nickname with current price")
                    logger.info(f"Updated nickname to: PDT ${price:.4f} "
                              f"{'📈' if change_24h >= 0 else '📉'}")

            except Exception as e:
                print(f"Error accessing guild: {e}")
                
            print("Updating status...")
            
            status_text = f"24h: {change_24h:+.2f}%"
            
            # Then set new activity
            await self._discord_client.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=status_text
                )
            )
            print(f"Status updated to: {status_text}")
            logger.info(f"Status updated: {status_text}")
            
            print(f"Next update in {self.update_interval} seconds")
            print("Successfully updated status")

            self._previous_price = price

        except Exception as e:
            print(f"\nError updating price: {type(e).__name__}: {str(e)}")

    def setup_discord_bot(self):
        print("\nChecking Discord permissions...")
        
        @self._discord_client.event
        async def on_ready():
            print(f'Bot logged in as {self._discord_client.user}')
            print(f"Bot is in guilds: {[g.name for g in self._discord_client.guilds]}")
            if not self._price_update_loop:
                # Check bot's role position
                for guild in self._discord_client.guilds:
                    bot_member = guild.get_member(self._discord_client.user.id)
                    if bot_member:
                        bot_role = bot_member.top_role
                        logger.info(f"\nChecking bot role in {guild.name}:")
                        logger.info(f"Bot role: {bot_role.name} (position: {bot_role.position})")
                        
                        # Check if any roles are above bot's role
                        higher_roles = [r for r in guild.roles if r.position > bot_role.position]
                        if higher_roles:
                            logger.warning("WARNING: These roles are above the bot's role:")
                            for role in higher_roles:
                                logger.warning(f"- {role.name} (position: {role.position})")
                            logger.warning("Consider moving the bot's role higher for better functionality")

                # First clear any existing activity
                await self._discord_client.change_presence(activity=None, status=discord.Status.online)
                await asyncio.sleep(1)  # Wait a second

                # Then set initial activity
                await self._discord_client.change_presence(
                    status=discord.Status.online,
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name="Loading PDT Tracker..."
                    )
                )
                print("Initial status set")
                    
                # Then start the price update loop
                self.price_update_loop = self.create_price_loop()
                self.price_update_loop.start()
                print("Price update loop started")
                print("Waiting for first price update...")

    def run(self):
        """
        Start the Discord bot and price tracking
        """
        print("Checking Discord token...")
        if not DISCORD_TOKEN or DISCORD_TOKEN == "your_discord_bot_token":
            raise ValueError(
                "Invalid Discord token. Please update your .env file with a valid token from "
                "https://discord.com/developers/applications"
            )
        
        print("Starting bot...")
        print(f"Using guild ID: {GUILD_ID}")
        
        print("Connecting to Discord...")
        self._discord_client.run(DISCORD_TOKEN)
        return "Bot started successfully" 

    async def force_status_update(self, text: str):
        """Force update the bot's status"""
        try:
            # First clear any existing activity
            await self._discord_client.change_presence(activity=None)
            await asyncio.sleep(1)  # Wait a second

            # Then set new activity
            await self._discord_client.change_presence(
                status=discord.Status.online,
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=text
                )
            )
            print(f"Forced status update to: {text}")
        except Exception as e:
            print(f"Error forcing status update: {str(e)}") 