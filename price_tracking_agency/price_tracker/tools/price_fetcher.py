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
ROLE_NAME = "PDT Price"

class PriceTrackerTool(BaseTool):
    """
    Tool for tracking PDT-Token price and updating Discord role/status
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    update_interval: int = Field(
        default=300,  # 5 minutes
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
        loop = tasks.loop(seconds=self.update_interval)(self.price_update_loop_func)
        return loop

    async def ensure_guild_access(self):
        guild = self._discord_client.get_guild(GUILD_ID)
        if not guild:
            print("\nERROR: Bot is not in the specified guild!")
            print(f"Guild ID: {GUILD_ID}")
            print("\nTo fix this:")
            print("1. Go to https://discord.com/developers/applications")
            print("2. Select your bot -> OAuth2 -> URL Generator")
            print("3. Select scopes: bot, applications.commands")
            print("4. Select permissions: Manage Roles, Change Nickname, View Channels")
            print("5. Copy the generated URL")
            print("6. Open the URL in your browser and add the bot to your server")
            print(f"Available guilds: {[g.name for g in self._discord_client.guilds]}")
            raise ValueError(f"Bot is not in guild with ID {GUILD_ID}")

    async def price_update_loop_func(self):
        try:
            # Fetch current price and 24h change from Coingecko
            print("Fetching price data...")
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/token_price/base?contract_addresses=0xeff2a458e464b07088bdb441c21a42ab4b61e07e&vs_currencies=usd&include_24hr_change=true"
            )
            data = response.json()
            
            price = data[PDT_CONTRACT.lower()]['usd']
            change_24h = data[PDT_CONTRACT.lower()]['usd_24h_change']

            # Get the guild and role
            await self.ensure_guild_access()
            guild = self._discord_client.get_guild(GUILD_ID)
            role = discord.utils.get(guild.roles, name=ROLE_NAME)

            # Create role if it doesn't exist
            if not role:
                try:
                    print(f"Creating role '{ROLE_NAME}'...")
                    # Check bot's permissions
                    bot_member = guild.get_member(self._discord_client.user.id)
                    if not bot_member.guild_permissions.administrator:
                        print("\nERROR: Bot needs Administrator permissions!")
                        print("Please reinvite the bot with Administrator permissions:")
                        print("1. Go to https://discord.com/developers/applications")
                        print("2. Select your bot -> OAuth2 -> URL Generator")
                        print("3. Select 'Administrator' under Bot Permissions")
                    role = await guild.create_role(
                        name=ROLE_NAME,
                        hoist=True,  # This makes the role show separately in member list
                        mentionable=True,
                        reason="PDT Price Tracking Role"
                    )
                    # Move the role to the top of the hierarchy
                    await role.edit(position=len(guild.roles) - 1)
                    bot_member = guild.get_member(self._discord_client.user.id)
                    await bot_member.add_roles(role)
                except discord.errors.Forbidden as e:
                    print("\nERROR: Bot doesn't have permission to manage roles!")
                    print("Please make sure the bot has Administrator permissions.")
                    raise e
                except Exception as e:
                    print(f"Error creating role: {e}")
                    raise e

            # Update role color based on price change
            color = discord.Color.green() if change_24h >= 0 else discord.Color.red()
            await role.edit(color=color)

            # Update role name with current price
            new_name = f"PDT: ${price:.4f}"
            await role.edit(name=new_name)

            # Update bot's nickname to match role name
            bot_member = guild.get_member(self._discord_client.user.id)
            await bot_member.edit(nick=new_name)

            # Update bot's status with 24h change
            status_text = f"24h: {change_24h:+.2f}%"
            await self._discord_client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=status_text
                )
            )

            self._previous_price = price

        except Exception as e:
            print(f"Error updating price: {e}")

    def setup_discord_bot(self):
        print("\nChecking Discord permissions...")
        @self._discord_client.event
        async def on_ready():
            print(f'Bot logged in as {self._discord_client.user}')
            print(f"Bot is in guilds: {[g.name for g in self._discord_client.guilds]}")
            if not self._price_update_loop:
                self.price_update_loop = self.create_price_loop()
                self.price_update_loop.start()
            
            # Check bot permissions
            for guild in self._discord_client.guilds:
                bot_member = guild.get_member(self._discord_client.user.id)
                if not bot_member.guild_permissions.administrator:
                    print(f"\nWARNING: Bot doesn't have Administrator permissions in {guild.name}")
                    print("Some features may not work correctly.")
                    print("Please reinvite the bot with Administrator permissions.")

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
        
        self._discord_client.run(DISCORD_TOKEN)
        return "Bot started successfully" 