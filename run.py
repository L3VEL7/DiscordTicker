import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool

def main():
    tool = PriceTrackerTool()
    tool.run()

if __name__ == "__main__":
    main() 