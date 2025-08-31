from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with comprehensive sample data for all features'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating comprehensive sample data...')
        
        # Import models
        from charts.models import Market, ChartPrediction, Contest, ContestParticipation
        from payments.models import SubscriptionPlan, Payment
        from users.models import Coupon, SocialPromotion, AppSettings
        from notifications.models import NotificationTemplate, UserNotificationSettings
        
        # Create markets for all supported regions
        self.create_markets()
        
        # Create subscription plans
        self.create_subscription_plans()
        
        # Create sample users with different types
        self.create_sample_users()
        
        # Create notification templates
        self.create_notification_templates()
        
        # Create sample predictions
        self.create_sample_predictions()
        
        # Create contests
        self.create_contests()
        
        # Create coupons
        self.create_coupons()
        
        # Create app settings
        self.create_app_settings()
        
        self.stdout.write(self.style.SUCCESS('Successfully created comprehensive sample data'))
    
    def create_markets(self):
        """Create markets for different regions"""
        from charts.models import Market
        
        markets_data = [
            # US Stocks
            ('AAPL', 'Apple Inc.', 'us_stock', 'AAPL'),
            ('GOOGL', 'Alphabet Inc.', 'us_stock', 'GOOGL'),
            ('MSFT', 'Microsoft Corporation', 'us_stock', 'MSFT'),
            ('TSLA', 'Tesla Inc.', 'us_stock', 'TSLA'),
            ('AMZN', 'Amazon.com Inc.', 'us_stock', 'AMZN'),
            
            # Korean Stocks
            ('005930', 'Samsung Electronics', 'kr_stock', '005930.KS'),
            ('000660', 'SK Hynix', 'kr_stock', '000660.KS'),
            ('035420', 'NAVER Corporation', 'kr_stock', '035420.KS'),
            
            # Japanese Stocks
            ('7203', 'Toyota Motor Corporation', 'jp_stock', '7203.T'),
            ('9984', 'SoftBank Group Corp', 'jp_stock', '9984.T'),
            
            # Cryptocurrencies
            ('BTC', 'Bitcoin', 'crypto', 'bitcoin'),
            ('ETH', 'Ethereum', 'crypto', 'ethereum'),
            ('ADA', 'Cardano', 'crypto', 'cardano'),
            
            # European Stocks
            ('SAP', 'SAP SE', 'de_stock', 'SAP.DE'),
            ('ASML', 'ASML Holding', 'de_stock', 'ASML.AS'),
            
            # UK Stocks
            ('SHEL', 'Shell plc', 'uk_stock', 'SHEL.L'),
            ('BP', 'BP p.l.c.', 'uk_stock', 'BP.L'),
            
            # Canadian Stocks
            ('SHOP', 'Shopify Inc.', 'ca_stock', 'SHOP.TO'),
            
            # Indian Stocks
            ('RELIANCE', 'Reliance Industries', 'in_stock', 'RELIANCE.NS'),
            ('TCS', 'Tata Consultancy Services', 'in_stock', 'TCS.NS'),
        ]
        
        for symbol, name, market_type, api_symbol in markets_data:
            Market.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': name,
                    'market_type': market_type,
                    'api_symbol': api_symbol,
                    'description': f'{name} - {market_type.replace("_", " ").title()}',
                    'is_active': True,
                }
            )
        
        self.stdout.write(f'Created {len(markets_data)} markets')
    
    def create_subscription_plans(self):
        """Create subscription plans"""
        from payments.models import SubscriptionPlan
        
        plans_data = [
            ('Free Plan', 'free', Decimal('0.00'), 0, ['3 chart views', 'Basic predictions', 'Limited board access']),
            ('Monthly Premium', 'monthly', Decimal('19.99'), 30, ['Unlimited chart views', 'Advanced predictions', 'Full board access', 'Contest participation']),
            ('Yearly Premium', 'yearly', Decimal('199.99'), 365, ['Unlimited chart views', 'Advanced predictions', 'Full board access', 'Contest participation', '2 months free']),
            ('Lifetime Premium', 'lifetime', Decimal('999.99'), 0, ['Unlimited access', 'All features', 'Priority support', 'Beta features']),
        ]
        
        for name, plan_type, price, duration, features in plans_data:
            SubscriptionPlan.objects.get_or_create(
                plan_type=plan_type,
                defaults={
                    'name': name,
                    'price': price,
                    'duration_days': duration,
                    'features': features,
                    'is_active': True,
                }
            )
        
        self.stdout.write('Created subscription plans')
    
    def create_sample_users(self):
        """Create sample users with different types"""
        users_data = [
            ('john@example.com', 'john_trader', 'free', 'John Doe'),
            ('sarah@example.com', 'sarah_investor', 'premium', 'Sarah Smith'),
            ('mike@example.com', 'mike_analyst', 'premium', 'Mike Johnson'),
            ('emma@example.com', 'emma_crypto', 'free', 'Emma Wilson'),
            ('alex@example.com', 'alex_stocks', 'premium', 'Alex Brown'),
        ]
        
        for email, username, user_type, full_name in users_data:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password='password123',
                    user_type=user_type,
                    first_name=full_name.split()[0],
                    last_name=full_name.split()[1],
                )
                
                if user_type == 'premium':
                    user.premium_subscription_date = timezone.now()
                    user.premium_expiry_date = timezone.now() + timedelta(days=30)
                    user.free_visits_remaining = 999
                
                user.referral_code = f"REF{user.id:06d}"
                user.save()
                
                # Create notification settings
                from notifications.models import UserNotificationSettings
                UserNotificationSettings.objects.get_or_create(user=user)
        
        self.stdout.write('Created sample users')
    
    def create_notification_templates(self):
        """Create notification templates"""
        from notifications.models import NotificationTemplate
        
        templates_data = [
            ('welcome_email', 'Welcome to Stock Chart Prediction!', 
             'Welcome {{user.username}}! Start your trading journey with us.', 'email'),
            ('prediction_reminder', 'Your prediction is due soon!', 
             'Your {{symbol}} prediction expires on {{date}}.', 'email'),
            ('contest_winner', 'Congratulations! You won a contest!', 
             'You placed {{rank}} in {{contest_name}} contest!', 'email'),
            ('low_visits_warning', 'Your free visits are running low', 
             'You have {{visits}} free visits remaining. Upgrade now!', 'email'),
        ]
        
        for name, subject, message, notif_type in templates_data:
            NotificationTemplate.objects.get_or_create(
                name=name,
                defaults={
                    'subject_template': subject,
                    'message_template': message,
                    'notification_type': notif_type,
                }
            )
        
        self.stdout.write('Created notification templates')
    
    def create_sample_predictions(self):
        """Create sample predictions"""
        from charts.models import Market, ChartPrediction
        
        markets = Market.objects.all()[:10]
        users = User.objects.all()
        
        for i in range(20):
            market = random.choice(markets)
            user = random.choice(users)
            
            current_price = Decimal(str(random.uniform(50, 500)))
            predicted_price = current_price * Decimal(str(random.uniform(0.8, 1.2)))
            
            target_date = timezone.now() + timedelta(days=random.randint(1, 30))
            
            ChartPrediction.objects.create(
                user=user,
                market=market,
                target_date=target_date,
                current_price=current_price,
                predicted_price=predicted_price,
                duration_days=random.randint(1, 30),
                confidence_level=random.randint(60, 95),
                notes=f"Sample prediction for {market.symbol}",
                is_public=random.choice([True, False]),
            )
        
        self.stdout.write('Created sample predictions')
    
    def create_contests(self):
        """Create sample contests"""
        from charts.models import Contest
        
        Contest.objects.get_or_create(
            title="Monthly Trading Challenge",
            defaults={
                'description': 'Predict the best performing stocks this month and win prizes!',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'prize_pool': Decimal('1000.00'),
                'entry_fee': Decimal('0.00'),
                'max_participants': 100,
                'rules': 'Make accurate predictions to win prizes. Top 3 winners get cash rewards.',
            }
        )
        
        self.stdout.write('Created sample contests')
    
    def create_coupons(self):
        """Create sample coupons"""
        from users.models import Coupon
        
        coupons_data = [
            ('WELCOME10', 'free_days', Decimal('7'), 'Welcome bonus'),
            ('SOCIAL20', 'percentage', Decimal('20'), 'Social media promotion'),
            ('NEWUSER', 'free_predictions', Decimal('5'), 'New user bonus'),
        ]
        
        for code, coupon_type, value, description in coupons_data:
            Coupon.objects.get_or_create(
                code=code,
                defaults={
                    'coupon_type': coupon_type,
                    'value': value,
                    'max_uses': 100,
                    'expiry_date': timezone.now() + timedelta(days=30),
                }
            )
        
        self.stdout.write('Created sample coupons')
    
    def create_app_settings(self):
        """Create application settings"""
        from users.models import AppSettings
        
        settings_data = [
            ('maintenance_mode', 'false', 'Enable maintenance mode'),
            ('free_user_chart_limit', '3', 'Number of free chart views for new users'),
            ('contest_enabled', 'true', 'Enable contest functionality'),
            ('referral_commission_rate', '0.15', 'Commission rate for referrals'),
            ('max_predictions_per_day', '10', 'Maximum predictions per user per day'),
        ]
        
        for key, value, description in settings_data:
            AppSettings.objects.get_or_create(
                key=key,
                defaults={
                    'value': value,
                    'description': description,
                }
            )
        
        self.stdout.write('Created app settings')
