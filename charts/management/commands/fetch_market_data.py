"""
Management command to fetch real-time market data from external APIs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from charts.models import Market, StockData
from decimal import Decimal
import requests
import json
import time
import random

class Command(BaseCommand):
    help = 'Fetch real-time market data from external APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Specific symbol to update (optional)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Update interval in seconds (default: 60)',
        )

    def handle(self, *args, **options):
        symbol = options.get('symbol')
        interval = options.get('interval')

        self.stdout.write(
            self.style.SUCCESS(f'Starting market data fetcher (interval: {interval}s)')
        )

        if symbol:
            self.update_single_market(symbol)
        else:
            # Update all markets in a loop
            while True:
                self.update_all_markets()
                self.stdout.write(f'Sleeping for {interval} seconds...')
                time.sleep(interval)

    def update_single_market(self, symbol):
        """Update data for a single market"""
        try:
            market = Market.objects.get(symbol=symbol.upper())
            data = self.fetch_market_data(market.symbol)
            if data:
                self.save_market_data(market, data)
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {market.symbol}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to fetch data for {market.symbol}')
                )
        except Market.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Market {symbol} not found')
            )

    def update_all_markets(self):
        """Update data for all markets"""
        markets = Market.objects.all()
        updated_count = 0
        
        for market in markets:
            try:
                data = self.fetch_market_data(market.symbol)
                if data:
                    self.save_market_data(market, data)
                    updated_count += 1
                time.sleep(1)  # Rate limiting
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating {market.symbol}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated {updated_count} markets')
        )

    def fetch_market_data(self, symbol):
        """
        Fetch market data from external API
        Using Alpha Vantage free tier as an example
        """
        # Alpha Vantage Free API (requires registration for API key)
        # API_KEY = 'YOUR_ALPHA_VANTAGE_API_KEY'
        # url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}'
        
        # For demo purposes, we'll use mock data with realistic patterns
        return self.generate_realistic_mock_data(symbol)

    def generate_realistic_mock_data(self, symbol):
        """
        Generate realistic mock data for demonstration
        In production, replace this with actual API calls
        """
        # Base prices for different asset types
        base_prices = {
            'BTC': 45000, 'ETH': 3200, 'ADA': 1.20, 'DOT': 25.50,
            'AAPL': 175, 'GOOGL': 2800, 'MSFT': 350, 'AMZN': 3400,
            'TSLA': 800, 'NVDA': 450, 'META': 320, 'NFLX': 600,
            'EUR': 1.18, 'GBP': 1.35, 'JPY': 0.009, 'CHF': 1.08,
            'GOLD': 1950, 'SILVER': 24.50, 'OIL': 85, 'GAS': 4.20
        }
        
        base_price = base_prices.get(symbol, random.uniform(50, 500))
        
        # Add realistic volatility
        volatility = random.uniform(-0.05, 0.05)  # -5% to +5%
        current_price = base_price * (1 + volatility)
        
        # Generate OHLC data
        high = current_price * random.uniform(1.001, 1.02)
        low = current_price * random.uniform(0.98, 0.999)
        open_price = current_price * random.uniform(0.995, 1.005)
        
        # Volume varies by asset type
        if symbol in ['BTC', 'ETH']:
            volume = random.randint(500000, 2000000)
        elif symbol in ['AAPL', 'GOOGL', 'MSFT']:
            volume = random.randint(5000000, 50000000)
        else:
            volume = random.randint(100000, 1000000)

        return {
            'symbol': symbol,
            'open': open_price,
            'high': high,
            'low': low,
            'close': current_price,
            'volume': volume,
            'timestamp': timezone.now()
        }

    def save_market_data(self, market, data):
        """Save market data to database"""
        StockData.objects.create(
            market=market,
            open_price=Decimal(str(round(data['open'], 2))),
            high_price=Decimal(str(round(data['high'], 2))),
            low_price=Decimal(str(round(data['low'], 2))),
            close_price=Decimal(str(round(data['close'], 2))),
            volume=data['volume'],
            timestamp=data['timestamp']
        )

    def fetch_from_yahoo_finance(self, symbol):
        """
        Alternative: Fetch from Yahoo Finance (free but rate limited)
        """
        try:
            # Yahoo Finance API endpoint (unofficial)
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data['chart']['result'][0]
                meta = result['meta']
                
                return {
                    'symbol': symbol,
                    'open': meta.get('previousClose', 100),
                    'high': meta.get('regularMarketDayHigh', 102),
                    'low': meta.get('regularMarketDayLow', 98),
                    'close': meta.get('regularMarketPrice', 100),
                    'volume': meta.get('regularMarketVolume', 1000000),
                    'timestamp': timezone.now()
                }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Yahoo Finance API error for {symbol}: {str(e)}')
            )
            return None

    def fetch_from_alpha_vantage(self, symbol, api_key):
        """
        Fetch from Alpha Vantage (requires API key)
        """
        try:
            url = f'https://www.alphavantage.co/query'
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    return {
                        'symbol': symbol,
                        'open': float(quote.get('02. open', 0)),
                        'high': float(quote.get('03. high', 0)),
                        'low': float(quote.get('04. low', 0)),
                        'close': float(quote.get('05. price', 0)),
                        'volume': int(quote.get('06. volume', 0)),
                        'timestamp': timezone.now()
                    }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Alpha Vantage API error for {symbol}: {str(e)}')
            )
            return None

    def fetch_crypto_data(self, symbol):
        """
        Fetch cryptocurrency data from CoinGecko (free API)
        """
        try:
            # Remove common suffixes
            clean_symbol = symbol.replace('USD', '').replace('USDT', '')
            
            # CoinGecko API
            url = f'https://api.coingecko.com/api/v3/simple/price'
            params = {
                'ids': clean_symbol.lower(),
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if clean_symbol.lower() in data:
                    price_data = data[clean_symbol.lower()]
                    current_price = price_data['usd']
                    
                    # Estimate OHLC from current price
                    change_24h = price_data.get('usd_24h_change', 0) / 100
                    open_price = current_price / (1 + change_24h)
                    
                    return {
                        'symbol': symbol,
                        'open': open_price,
                        'high': current_price * 1.01,
                        'low': current_price * 0.99,
                        'close': current_price,
                        'volume': price_data.get('usd_24h_vol', 1000000),
                        'timestamp': timezone.now()
                    }
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'CoinGecko API error for {symbol}: {str(e)}')
            )
            return None
