from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Market(models.Model):
    """Different markets available for trading"""
    MARKET_TYPES = (
        ('crypto', 'Cryptocurrency'),
        ('us_stock', 'US Stock'),
        ('kr_stock', 'Korean Stock'),
        ('jp_stock', 'Japanese Stock'),
        ('in_stock', 'Indian Stock'),
        ('uk_stock', 'UK Stock'),
        ('ca_stock', 'Canadian Stock'),
        ('fr_stock', 'French Stock'),
        ('de_stock', 'German Stock'),
        ('tw_stock', 'Taiwanese Stock'),
    )
    
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, unique=True)
    market_type = models.CharField(max_length=20, choices=MARKET_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    api_symbol = models.CharField(max_length=50, help_text="Symbol used in API calls")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    class Meta:
        ordering = ['symbol']

class StockData(models.Model):
    """Historical and real-time stock data"""
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='stock_data')
    timestamp = models.DateTimeField()
    open_price = models.DecimalField(max_digits=15, decimal_places=4)
    high_price = models.DecimalField(max_digits=15, decimal_places=4)
    low_price = models.DecimalField(max_digits=15, decimal_places=4)
    close_price = models.DecimalField(max_digits=15, decimal_places=4)
    volume = models.BigIntegerField()
    market_cap = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('market', 'timestamp')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.market.symbol} - {self.timestamp.date()}"

class ChartPrediction(models.Model):
    """User predictions for future stock prices"""
    PREDICTION_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField(auto_now_add=True)
    target_date = models.DateTimeField()
    current_price = models.DecimalField(max_digits=15, decimal_places=4)
    predicted_price = models.DecimalField(max_digits=15, decimal_places=4)
    actual_price = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    accuracy_percentage = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PREDICTION_STATUS, default='pending')
    duration_days = models.IntegerField()
    confidence_level = models.IntegerField(choices=[(i, f"{i}%") for i in range(1, 101)], default=50)
    notes = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    likes_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.market.symbol} prediction"
    
    def calculate_accuracy(self):
        """Calculate accuracy percentage when actual price is available"""
        if self.actual_price and self.predicted_price and self.current_price:
            predicted_change = abs(self.predicted_price - self.current_price)
            actual_change = abs(self.actual_price - self.current_price)
            
            if predicted_change == 0:
                self.accuracy_percentage = 100.0 if actual_change == 0 else 0.0
            else:
                error_rate = abs(predicted_change - actual_change) / predicted_change
                self.accuracy_percentage = max(0, 100 - (error_rate * 100))
            
            self.save()
    
    def is_prediction_due(self):
        """Check if prediction target date has passed"""
        return timezone.now() >= self.target_date
    
    class Meta:
        ordering = ['-created_at']

class ChartComment(models.Model):
    """Comments on chart predictions"""
    prediction = models.ForeignKey(ChartPrediction, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.prediction.market.symbol}"
    
    class Meta:
        ordering = ['-created_at']

class ChartLike(models.Model):
    """Like system for chart predictions"""
    prediction = models.ForeignKey(ChartPrediction, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('prediction', 'user')
    
    def __str__(self):
        return f"{self.user.email} likes {self.prediction.market.symbol}"

class TechnicalIndicator(models.Model):
    """Technical analysis indicators for charts"""
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='indicators')
    indicator_type = models.CharField(max_length=50, choices=[
        ('sma', 'Simple Moving Average'),
        ('ema', 'Exponential Moving Average'),
        ('rsi', 'Relative Strength Index'),
        ('macd', 'MACD'),
        ('bollinger', 'Bollinger Bands'),
        ('stochastic', 'Stochastic Oscillator'),
    ])
    period = models.IntegerField()
    value = models.DecimalField(max_digits=15, decimal_places=4)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('market', 'indicator_type', 'period', 'timestamp')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.market.symbol} - {self.indicator_type} ({self.period})"

class Contest(models.Model):
    """Trading contests and events"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2)
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_participants = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    rules = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class ContestParticipation(models.Model):
    """Track user participation in contests"""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prediction = models.ForeignKey(ChartPrediction, on_delete=models.CASCADE)
    final_accuracy = models.FloatField(null=True, blank=True)
    rank = models.IntegerField(null=True, blank=True)
    prize_won = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('contest', 'user')
    
    def __str__(self):
        return f"{self.user.email} in {self.contest.title}"
