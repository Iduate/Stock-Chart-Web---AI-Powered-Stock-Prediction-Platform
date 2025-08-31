from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid
import string
import random

class User(AbstractUser):
    """Custom User model with additional fields for the stock chart platform"""
    
    USER_TYPES = (
        ('free', 'Free User'),
        ('premium', 'Premium User'),
        ('admin', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='free')
    free_visits_remaining = models.IntegerField(default=3)
    premium_subscription_date = models.DateTimeField(null=True, blank=True)
    premium_expiry_date = models.DateTimeField(null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    total_accuracy_rate = models.FloatField(default=0.0)
    total_predictions = models.IntegerField(default=0)
    earnings_from_referrals = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    country = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    def is_premium(self):
        """Check if user has active premium subscription"""
        if self.user_type == 'premium' and self.premium_expiry_date:
            return self.premium_expiry_date > timezone.now()
        return False
    
    def can_access_premium_content(self):
        """Check if user can access premium content"""
        if self.is_premium():
            return True
        return self.free_visits_remaining > 0
    
    def consume_free_visit(self):
        """Consume one free visit"""
        if self.free_visits_remaining > 0:
            self.free_visits_remaining -= 1
            self.save()
    
    def update_accuracy_rate(self, new_prediction_accuracy):
        """Update user's overall accuracy rate"""
        total_score = self.total_accuracy_rate * self.total_predictions
        self.total_predictions += 1
        self.total_accuracy_rate = (total_score + new_prediction_accuracy) / self.total_predictions
        self.save()

class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    social_media_links = models.JSONField(default=dict, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    trading_experience = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ], default='beginner')
    favorite_markets = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} Profile"

class ReferralSystem(models.Model):
    """Track referral system and earnings"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_made')
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referred_by')
    referral_date = models.DateTimeField(auto_now_add=True)
    commission_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('referrer', 'referred_user')
    
    def __str__(self):
        return f"{self.referrer.email} referred {self.referred_user.email}"

class Coupon(models.Model):
    """Coupon system for promotional activities"""
    COUPON_TYPES = (
        ('free_days', 'Free Premium Days'),
        ('percentage', 'Percentage Discount'),
        ('fixed_amount', 'Fixed Amount Discount'),
        ('free_predictions', 'Free Predictions'),
    )
    
    code = models.CharField(max_length=20, unique=True)
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount or percentage")
    max_uses = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Coupon: {self.code}"
    
    def is_valid(self):
        """Check if coupon is still valid"""
        return (self.is_active and 
                self.used_count < self.max_uses and 
                self.expiry_date > timezone.now())
    
    @classmethod
    def generate_code(cls, length=8):
        """Generate a random coupon code"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

class CouponUsage(models.Model):
    """Track coupon usage by users"""
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('coupon', 'user')
    
    def __str__(self):
        return f"{self.user.email} used {self.coupon.code}"

class SocialPromotion(models.Model):
    """Track social media promotions and rewards"""
    PLATFORM_CHOICES = (
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_promotions')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    post_url = models.URLField()
    verification_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ], default='pending')
    reward_given = models.BooleanField(default=False)
    reward_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.platform} promotion"

class UserAccessLog(models.Model):
    """Log user access to premium content"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_logs')
    content_type = models.CharField(max_length=50, choices=[
        ('chart_view', 'Chart View'),
        ('prediction_view', 'Prediction View'),
        ('board_access', 'Board Access'),
        ('ranking_view', 'Ranking View'),
        ('contest_view', 'Contest View'),
    ])
    content_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.content_type}"
    
    class Meta:
        ordering = ['-accessed_at']

class UserSubscriptionHistory(models.Model):
    """Track user subscription history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_history')
    subscription_type = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renewal = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=20)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_type}"
    
    class Meta:
        ordering = ['-created_at']

class AppSettings(models.Model):
    """Global application settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Setting: {self.key}"
    
    class Meta:
        verbose_name = "App Setting"
        verbose_name_plural = "App Settings"
