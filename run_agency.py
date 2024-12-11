import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from price_tracking_agency.agency import agency

if __name__ == "__main__":
    agency.run_demo() 