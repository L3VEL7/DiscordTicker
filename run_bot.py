import os
import sys
from pathlib import Path
import logging
import discord

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') == '1' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PDTBot')

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool

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
        tool = PriceTrackerTool()
        tool.run()
    except discord.LoginFailure:
        logger.error("Failed to login. Please check your Discord token.")
    except discord.PrivilegedIntentsRequired:
        logger.error("Bot requires privileged intents. Please enable them in Discord Developer Portal.")
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)

if __name__ == "__main__":
    main() 