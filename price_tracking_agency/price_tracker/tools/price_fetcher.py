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

    async def check_bot_permissions(self, guild):
        """Check if bot has all required permissions"""
        bot_member = guild.get_member(self._discord_client.user.id)
        bot_role = bot_member.top_role
        
        print("\nChecking bot permissions in detail:")
        print(f"Bot's highest role: {bot_role.name} (position {bot_role.position})")
        
        # Check role hierarchy
        price_role = discord.utils.get(guild.roles, name=ROLE_NAME)
        if price_role and bot_role.position < price_role.position:
            print("\nERROR: Bot's role is below the price role!")
            print(f"Bot role '{bot_role.name}' position: {bot_role.position}")
            print(f"Price role '{price_role.name}' position: {price_role.position}")
            print("\nTo fix this:")
            print("1. Go to Server Settings -> Roles")
            print("2. Drag the 'PDTbot' role ABOVE the 'PDT Price' role")
            return False

        print("Current permissions:")
        permissions = {
            'manage_roles': bot_member.guild_permissions.manage_roles,
            'change_nickname': bot_member.guild_permissions.change_nickname,
            'view_channel': bot_member.guild_permissions.view_channel
        }
        for perm, value in permissions.items():
            print(f"- {perm}: {'✅' if value else '❌'}")
        
        return all(permissions.values())  # Return True only if we have all permissions

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
            
            # Check permissions before proceeding
            has_permissions = await self.check_bot_permissions(guild)
            if not has_permissions:
                print("\nPlease fix the bot's permissions before continuing.")
                print("The bot needs: Manage Roles, Change Nickname, View Channels")
                return

            # Debug: Print bot's role info
            bot_member = guild.get_member(self._discord_client.user.id)
            bot_role = bot_member.top_role
            print("\nBot role information:")
            print(f"Role name: {bot_role.name}")
            print(f"Role position: {bot_role.position}")
            print(f"Bot is server owner: {guild.owner_id == self._discord_client.user.id}")
            print(f"Role permissions: {bot_role.permissions}")
            print("\nServer roles (top to bottom):")
            for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
                print(f"- {r.name} (position: {r.position})")

            role = discord.utils.get(guild.roles, name=ROLE_NAME)

            # Create role if it doesn't exist
            if not role:
                try:
                    print(f"Creating role '{ROLE_NAME}'...")
                    print("Checking bot's role position...")
                    # Check specific required permissions
                    bot_member = guild.get_member(self._discord_client.user.id)
                    required_permissions = {
                        'manage_roles': 'Manage Roles',
                        'change_nickname': 'Change Nickname',
                        'view_channel': 'View Channels'
                    }
                    missing_permissions = [perm_name for perm, perm_name in required_permissions.items() 
                                         if not getattr(bot_member.guild_permissions, perm)]
                    if missing_permissions:
                        print("\nERROR: Bot is missing required permissions!")
                        print(f"Missing: {', '.join(missing_permissions)}")
                        print("\nTo fix this:")
                        print("1. Go to your Discord server settings")
                        print("2. Go to Roles")
                        print("3. Find and edit the bot's role")
                        print("4. Enable the following permissions: Manage Roles, Change Nickname, View Channels")
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
                    print(f"Successfully created role '{ROLE_NAME}' at position {role.position}")
                except discord.errors.Forbidden as e:
                    print("\nERROR: Bot doesn't have the required permissions!")
                    print("\nTo fix this, either:")
                    print("1. Fix the role hierarchy:")
                    print("   - Go to Server Settings -> Roles")
                    print("   - Find the bot's role (usually named 'PDTbot')")
                    print("   - Drag it ABOVE where the 'PDT Price' role will be created")
                    print("   - The order should be:")
                    print("     PDTbot")
                    print("     PDT Price")
                    print("     @everyone")
                    print(f"\nError details: {str(e)}")
                    print("2. Reinvite the bot with the correct permissions using the URL from the bot's developer portal")
                except Exception as e:
                    print(f"Error creating role: {e}")
                    raise e

            # Update role color based on price change
            color = discord.Color.green() if change_24h >= 0 else discord.Color.red()
            print(f"\nAttempting to edit role...")
            
            # Double check role hierarchy before editing
            if bot_role.position < role.position:
                print(f"\nERROR: Cannot edit role - bot's role ({bot_role.position}) is below target role ({role.position})")
                print("Please move the bot's role higher in the server's role list")
                return
            
            print(f"\nUpdating role '{role.name}' (position: {role.position})")
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
            if isinstance(e, discord.errors.Forbidden):
                print("\nERROR: Bot lacks required permissions!")
                print("Please ensure:")
                print("1. Bot's role is ABOVE the PDT Price role")
                print("2. Bot has Manage Roles permission")
                print("3. Bot has Change Nickname permission")
                print("4. Bot has View Channels permission")

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
            required_permissions = {
                'manage_roles': 'Manage Roles',
                'change_nickname': 'Change Nickname',
                'view_channel': 'View Channels'
            }

            for guild in self._discord_client.guilds:
                bot_member = guild.get_member(self._discord_client.user.id)
                missing_permissions = [perm_name for perm, perm_name in required_permissions.items() 
                                     if not getattr(bot_member.guild_permissions, perm, False)]
                if missing_permissions:
                    print(f"\nWARNING: Bot is missing permissions in {guild.name}")
                    print(f"Missing: {', '.join(missing_permissions)}")
                    print("\nTo fix this:")
                    print("1. Go to Server Settings -> Roles")
                    print("2. Find the bot's role (usually named 'PDTbot')")
                    print("3. Enable these permissions:")
                    print("Current permissions:")
                    for perm_name in missing_permissions:
                        print(f"   - {perm_name}")
 
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