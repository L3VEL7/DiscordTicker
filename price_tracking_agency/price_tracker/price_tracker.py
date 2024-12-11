from agency_swarm import Agent
from agency_swarm.util import set_openai_key
from price_tracking_agency.price_tracker.tools.price_fetcher import PriceTrackerTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
set_openai_key(os.getenv('OPENAI_API_KEY'))

class PriceTracker(Agent):
    def __init__(self):
        super().__init__(
            name="PriceTracker",
            description="Tracks PDT-Token price and updates Discord roles/status",
            instructions="./instructions.md",
            tools_folder="./tools",
            tools=[PriceTrackerTool],
            temperature=0.5,
        ) 

# Add a test case
if __name__ == "__main__":
    tracker = PriceTracker()
    print(f"Created PriceTracker agent: {tracker.name}")