from agency_swarm import Agency
from price_tracking_agency.price_tracker.price_tracker import PriceTracker

price_tracker = PriceTracker()

agency = Agency(
    [price_tracker],
    shared_instructions="agency_manifesto.md",
    temperature=0.5
)

if __name__ == "__main__":
    agency.run_demo() 