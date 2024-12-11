import os
import sys
import logging
import discord
from dotenv import load_dotenv
from web3 import Web3

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') == '1' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PDTBot')

# Load environment variables
load_dotenv()

class PDTBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.web3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        self.pdt_contract = self.web3.eth.contract(
            address='0x375488F097176507e39B9653b88FDc52cDE736Bf',
            abi=[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
                 {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        )
        
    async def setup_hook(self):
        self.update_price.start()

    @tasks.loop(minutes=5)
    async def update_price(self):
        """Update bot's nickname with current PDT price"""
        try:
            guild = self.get_guild(self.guild_id)
            if not guild:
                logger.error(f"Could not find guild with ID {self.guild_id}")
                return

            # Get PDT price from contract
            price = await self.get_pdt_price()
            
            # Update nickname with price
            await guild.me.edit(nick=f"PDT: ${price:.4f}")
            logger.info(f"Updated price to ${price:.4f}")

        except Exception as e:
            logger.error(f"Error updating price: {e}")

    async def get_pdt_price(self):
        """Get current PDT token price"""
        try:
            # Get price from contract
            decimals = self.pdt_contract.functions.decimals().call()
            total_supply = self.pdt_contract.functions.totalSupply().call()
            
            # Calculate price (implement your price calculation logic here)
            price = total_supply / (10 ** decimals)
            return price

        except Exception as e:
            logger.error(f"Error fetching price: {e}")
            return 0.0

def check_environment():
    """Check required environment variables"""
    required_vars = ['DISCORD_TOKEN', 'GUILD_ID']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

def main():
    """Run the price tracking bot"""
    logger.info("Starting PDT Price Tracking Bot...")
    
    # Check environment variables
    check_environment()
    
    try:
        bot = PDTBot()
        bot.run(os.getenv('DISCORD_TOKEN'))
    except discord.LoginFailure:
        logger.error("Failed to login. Please check your Discord token.")
    except discord.PrivilegedIntentsRequired:
        logger.error("Bot requires privileged intents. Please enable them in Discord Developer Portal.")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main() 