import os
import sys
from pathlib import Path
import argparse

# Add the project root to Python path
project_root = str(Path(__file__).parent)
sys.path.insert(0, project_root)

from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool
from price_tracking_agency.agency import agency

def run_bot():
    """Run the price tracking bot"""
    tool = PriceTrackerTool()
    try:
        print("Starting price tracking bot...")
        tool.run()
    except Exception as e:
        print(f"Error running bot: {e}")

def run_agency():
    """Run the full agency"""
    try:
        print("Starting agency...")
        agency.run_demo()
    except Exception as e:
        print(f"Error running agency: {e}")

def main():
    parser = argparse.ArgumentParser(description='Run PDT Price Tracking Bot')
    parser.add_argument('--mode', choices=['bot', 'agency'], default='bot',
                       help='Run mode: bot (price tracking only) or agency (full agency)')
    
    args = parser.parse_args()
    
    if args.mode == 'bot':
        run_bot()
    else:
        run_agency()

if __name__ == "__main__":
    main() 