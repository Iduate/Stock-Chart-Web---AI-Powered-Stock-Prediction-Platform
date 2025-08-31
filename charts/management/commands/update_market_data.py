from django.core.management.base import BaseCommand
from charts.market_api import MarketDataUpdater
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update market data for all active markets and check prediction accuracy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--markets-only',
            action='store_true',
            help='Only update market data, skip prediction accuracy checks',
        )
        parser.add_argument(
            '--predictions-only',
            action='store_true',
            help='Only check prediction accuracy, skip market data updates',
        )
    
    def handle(self, *args, **options):
        updater = MarketDataUpdater()
        
        if options['predictions_only']:
            self.stdout.write('Checking prediction accuracy...')
            updater.update_predictions_accuracy()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated prediction accuracy')
            )
        elif options['markets_only']:
            self.stdout.write('Updating market data...')
            updater.update_all_markets()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated market data')
            )
        else:
            self.stdout.write('Updating market data and checking predictions...')
            updater.update_all_markets()
            updater.update_predictions_accuracy()
            self.stdout.write(
                self.style.SUCCESS('Successfully updated market data and predictions')
            )
