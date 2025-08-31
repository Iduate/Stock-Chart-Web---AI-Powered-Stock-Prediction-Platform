from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

from charts.models import Market, StockData, Contest
from payments.models import SubscriptionPlan
from loans.models import SupportedCryptocurrency, LoanProduct

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create Markets
        markets_data = [
            # Cryptocurrencies
            ('BTC', 'Bitcoin', 'crypto', 'BTCUSD'),
            ('ETH', 'Ethereum', 'crypto', 'ETHUSD'),
            ('BNB', 'Binance Coin', 'crypto', 'BNBUSD'),
            ('ADA', 'Cardano', 'crypto', 'ADAUSD'),
            ('SOL', 'Solana', 'crypto', 'SOLUSD'),
            
            # US Stocks
            ('AAPL', 'Apple Inc.', 'us_stock', 'AAPL'),
            ('GOOGL', 'Alphabet Inc.', 'us_stock', 'GOOGL'),
            ('MSFT', 'Microsoft Corporation', 'us_stock', 'MSFT'),
            ('AMZN', 'Amazon.com Inc.', 'us_stock', 'AMZN'),
            ('TSLA', 'Tesla Inc.', 'us_stock', 'TSLA'),
            
            # Korean Stocks
            ('005930', 'Samsung Electronics', 'kr_stock', '005930.KS'),
            ('000660', 'SK Hynix', 'kr_stock', '000660.KS'),
            ('035420', 'NAVER Corporation', 'kr_stock', '035420.KS'),
            
            # Japanese Stocks
            ('7203', 'Toyota Motor Corp', 'jp_stock', '7203.T'),
            ('6758', 'Sony Group Corp', 'jp_stock', '6758.T'),
        ]
        
        for symbol, name, market_type, api_symbol in markets_data:
            market, created = Market.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'market_type': market_type,
                    'api_symbol': api_symbol,
                    'description': f'{name} trading on global markets',
                }
            )
            if created:
                self.stdout.write(f'Created market: {symbol}')
                
                # Create sample stock data
                self.create_sample_stock_data(market)
        
        # Create Subscription Plans
        plans_data = [
            ('Free Plan', 'free', Decimal('0.00'), 0, ['3 predictions per day', 'Basic charts', 'Community access']),
            ('Monthly Premium', 'monthly', Decimal('9.99'), 30, ['Unlimited predictions', 'Advanced charts', 'Real-time data', 'Contest access']),
            ('Yearly Premium', 'yearly', Decimal('99.99'), 365, ['All monthly features', '20% savings', 'Priority support']),
            ('Lifetime Premium', 'lifetime', Decimal('299.99'), 0, ['All features forever', 'Exclusive content', 'VIP support']),
        ]
        
        for name, plan_type, price, duration, features in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_type,
                defaults={
                    'name': name,
                    'price': price,
                    'duration_days': duration,
                    'features': features,
                }
            )
            if created:
                self.stdout.write(f'Created subscription plan: {name}')
        
        # Create Contests
        contest, created = Contest.objects.get_or_create(
            title='Weekly Trading Challenge',
            defaults={
                'description': 'Predict the weekly performance of top 10 stocks and win cash prizes!',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=7),
                'prize_pool': Decimal('1000.00'),
                'entry_fee': Decimal('10.00'),
                'max_participants': 100,
                'rules': 'Make predictions for at least 5 different stocks. Winners determined by accuracy.',
            }
        )
        if created:
            self.stdout.write('Created contest: Weekly Trading Challenge')
        
        # Create Supported Cryptocurrencies for loans
        crypto_data = [
            ('Bitcoin', 'BTC', 'bitcoin', Decimal('0.1'), 0.7, 0.85, Decimal('45000.00')),
            ('Ethereum', 'ETH', 'ethereum', Decimal('1.0'), 0.65, 0.80, Decimal('2800.00')),
            ('Binance Coin', 'BNB', 'binance_smart_chain', Decimal('10.0'), 0.6, 0.75, Decimal('320.00')),
            ('Cardano', 'ADA', 'ethereum', Decimal('1000.0'), 0.5, 0.65, Decimal('0.45')),
        ]
        
        for name, symbol, network, min_amount, ltv, liquidation, price in crypto_data:
            crypto, created = SupportedCryptocurrency.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'network': network,
                    'min_collateral_amount': min_amount,
                    'loan_to_value_ratio': ltv,
                    'liquidation_threshold': liquidation,
                    'current_price_usd': price,
                    'price_updated_at': timezone.now(),
                }
            )
            if created:
                self.stdout.write(f'Created supported crypto: {symbol}')
        
        # Create Loan Products
        loan_products_data = [
            ('Standard Crypto Loan', 'Get instant liquidity using your crypto as collateral', 
             Decimal('1000.00'), Decimal('50000.00'), 8.5, 30, 365),
            ('Premium Crypto Loan', 'Lower rates for premium users with higher collateral', 
             Decimal('5000.00'), Decimal('100000.00'), 6.5, 60, 730),
        ]
        
        for name, desc, min_loan, max_loan, rate, min_term, max_term in loan_products_data:
            product, created = LoanProduct.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'min_loan_amount': min_loan,
                    'max_loan_amount': max_loan,
                    'annual_interest_rate': rate,
                    'min_term_days': min_term,
                    'max_term_days': max_term,
                }
            )
            if created:
                self.stdout.write(f'Created loan product: {name}')
                # Add all supported cryptocurrencies to this product
                product.supported_cryptocurrencies.set(SupportedCryptocurrency.objects.all())
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))
    
    def create_sample_stock_data(self, market):
        """Create sample historical stock data"""
        base_price = Decimal(str(random.uniform(100, 1000)))
        current_time = timezone.now() - timedelta(days=30)
        
        for i in range(30):  # 30 days of data
            # Simulate price movement
            change_percent = random.uniform(-0.05, 0.05)  # ±5% daily change
            base_price *= Decimal(str(1 + change_percent))
            
            # Generate OHLC data
            open_price = base_price
            high_price = open_price * Decimal(str(1 + random.uniform(0, 0.03)))
            low_price = open_price * Decimal(str(1 - random.uniform(0, 0.03)))
            close_price = open_price + (open_price * Decimal(str(random.uniform(-0.02, 0.02))))
            
            volume = random.randint(10000, 1000000)
            
            StockData.objects.get_or_create(
                market=market,
                timestamp=current_time + timedelta(days=i),
                defaults={
                    'open_price': open_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'close_price': close_price,
                    'volume': volume,
                }
            )
            
            base_price = close_price
