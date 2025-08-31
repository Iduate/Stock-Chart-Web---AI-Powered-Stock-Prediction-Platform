from django.core.management.base import BaseCommand
from django.utils import timezone
from charts.models import Market, StockData
from charts.market_api import StockDataAPI
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetch real market data using your API keys and populate the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Fetch data for specific symbol only',
        )
        parser.add_argument(
            '--create-markets',
            action='store_true',
            help='Create popular market symbols if they don\'t exist',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Limit number of markets to process (default: 10)',
        )
    
    def handle(self, *args, **options):
        api = StockDataAPI()
        
        if options['create_markets']:
            self.create_popular_markets()
        
        if options['symbol']:
            # Fetch data for specific symbol
            market = Market.objects.filter(symbol=options['symbol']).first()
            if market:
                self.fetch_market_data(api, market)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Market with symbol {options["symbol"]} not found')
                )
        else:
            # Fetch data for all active markets
            markets = Market.objects.filter(is_active=True)[:options['limit']]
            self.stdout.write(f'Fetching data for {markets.count()} markets...')
            
            for market in markets:
                self.fetch_market_data(api, market)
                
        self.stdout.write(
            self.style.SUCCESS('Successfully completed market data fetch')
        )
    
    def create_popular_markets(self):
        """Create popular market symbols"""
        popular_stocks = [
            # US Tech Stocks
            ('AAPL', 'Apple Inc.', 'us_stock', 'AAPL'),
            ('MSFT', 'Microsoft Corporation', 'us_stock', 'MSFT'),
            ('GOOGL', 'Alphabet Inc.', 'us_stock', 'GOOGL'),
            ('AMZN', 'Amazon.com Inc.', 'us_stock', 'AMZN'),
            ('TSLA', 'Tesla Inc.', 'us_stock', 'TSLA'),
            ('META', 'Meta Platforms Inc.', 'us_stock', 'META'),
            ('NVDA', 'NVIDIA Corporation', 'us_stock', 'NVDA'),
            ('NFLX', 'Netflix Inc.', 'us_stock', 'NFLX'),
            
            # Traditional Stocks
            ('JPM', 'JPMorgan Chase & Co.', 'us_stock', 'JPM'),
            ('JNJ', 'Johnson & Johnson', 'us_stock', 'JNJ'),
            ('V', 'Visa Inc.', 'us_stock', 'V'),
            ('PG', 'Procter & Gamble', 'us_stock', 'PG'),
            
            # Cryptocurrencies (if supported)
            ('BTC-USD', 'Bitcoin', 'crypto', 'BTC-USD'),
            ('ETH-USD', 'Ethereum', 'crypto', 'ETH-USD'),
        ]
        
        created_count = 0
        for symbol, name, market_type, api_symbol in popular_stocks:
            market, created = Market.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'market_type': market_type,
                    'api_symbol': api_symbol,
                    'description': f'{name} - Real-time data',
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created market: {symbol} - {name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} new markets')
        )
    
    def fetch_market_data(self, api, market):
        """Fetch data for a specific market"""
        try:
            self.stdout.write(f'Fetching data for {market.symbol} ({market.name})...')
            
            # Get historical data
            data = api.get_stock_data(
                market.api_symbol, 
                market.market_type, 
                interval='1day',
                period='1month'
            )
            
            if data:
                saved_count = 0
                for data_point in data:
                    stock_data, created = StockData.objects.get_or_create(
                        market=market,
                        timestamp=data_point['timestamp'],
                        defaults={
                            'open_price': data_point['open'],
                            'high_price': data_point['high'],
                            'low_price': data_point['low'],
                            'close_price': data_point['close'],
                            'volume': data_point['volume'],
                        }
                    )
                    if created:
                        saved_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {market.symbol}: Saved {saved_count} new data points'
                    )
                )
                
                # Update market with latest price info
                if data:
                    latest = data[0]  # Most recent data point
                    self.stdout.write(
                        f'   Latest price: ${latest["close"]} (Volume: {latest["volume"]:,})'
                    )
                    
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  {market.symbol}: No data available')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ {market.symbol}: Error - {str(e)}')
            )
            logger.error(f'Error fetching data for {market.symbol}: {str(e)}')
