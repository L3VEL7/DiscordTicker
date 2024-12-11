import os
import sys
from pathlib import Path
import discord

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool

def main():
    """Run the price tracking bot"""
    print("Starting PDT Price Tracking Bot...")
    try:
        tool = PriceTrackerTool()
        tool.run()
    except discord.errors.PrivilegedIntentsRequired:
        print("\nERROR: Privileged Intents not enabled!")
        print("Please go to https://discord.com/developers/applications/")
        print("Select your bot -> Bot -> Privileged Gateway Intents")
        print("Enable: PRESENCE INTENT, SERVER MEMBERS INTENT, MESSAGE CONTENT INTENT")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 