"""
Background task to continuously update market data
This script can be run as a separate process or integrated with Celery
"""
import os
import sys
import django
import time
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockchart_project.settings')
django.setup()

from django.core.management import call_command
from charts.models import Market

def run_market_updater():
    """Run the market data updater in a loop"""
    print(f"Starting market data updater at {datetime.now()}")
    
    # Get all markets
    markets = Market.objects.all()
    print(f"Found {markets.count()} markets to update")
    
    while True:
        try:
            # Update each market
            for market in markets:
                print(f"Updating {market.symbol}...")
                call_command('fetch_market_data', symbol=market.symbol)
                time.sleep(2)  # Small delay between updates
            
            print(f"All markets updated at {datetime.now()}")
            print("Waiting 60 seconds before next update...")
            time.sleep(60)  # Wait 1 minute before next full update
            
        except KeyboardInterrupt:
            print("Market updater stopped by user")
            break
        except Exception as e:
            print(f"Error in market updater: {e}")
            time.sleep(30)  # Wait 30 seconds before retry

if __name__ == "__main__":
    run_market_updater()
