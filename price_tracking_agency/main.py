from price_tracking_agency.price_tracker import PriceTracker
from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool

def main():
    # Create and run the price tracker tool directly
    tool = PriceTrackerTool()
    tool.run()

if __name__ == "__main__":
    main() 