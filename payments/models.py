from django.db import models
from django.contrib.auth import get_user_model
import uuid
from decimal import Decimal

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Different subscription plans available"""
    PLAN_TYPES = (
        ('free', 'Free Plan'),
        ('monthly', 'Monthly Premium'),
        ('yearly', 'Yearly Premium'),
        ('lifetime', 'Lifetime Premium'),
    )
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(help_text="Duration in days, 0 for lifetime")
    features = models.JSONField(default=list)
    max_predictions = models.IntegerField(null=True, blank=True)
    max_chart_views = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)
    paypal_plan_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['price']

class Payment(models.Model):
    """Track all payments made by users"""
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    )
    
    PAYMENT_METHODS = (
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency'),
        ('coingate', 'CoinGate'),
        ('nowpayments', 'NOWPayments'),
        ('moonpay', 'MoonPay'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=200, unique=True)
    external_payment_id = models.CharField(max_length=200, blank=True)
    payment_data = models.JSONField(default=dict, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.subscription_plan.name} - ${self.amount}"
    
    class Meta:
        ordering = ['-created_at']

class Subscription(models.Model):
    """User subscriptions"""
    SUBSCRIPTION_STATUS = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='subscription')
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    auto_renewal = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    def is_active(self):
        from django.utils import timezone
        return self.status == 'active' and self.end_date > timezone.now()
    
    class Meta:
        ordering = ['-created_at']

class Invoice(models.Model):
    """Invoice generation for payments"""
    INVOICE_STATUS = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{self.pk or '0001'}"
        super().save(*args, **kwargs)

class RefundRequest(models.Model):
    """Handle refund requests"""
    REFUND_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refund_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=REFUND_STATUS, default='pending')
    admin_notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Refund request - {self.payment.transaction_id}"

class CryptoPayment(models.Model):
    """Handle cryptocurrency payments"""
    CRYPTO_STATUS = (
        ('pending', 'Pending'),
        ('confirming', 'Confirming'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    )
    
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='crypto_payment')
    cryptocurrency = models.CharField(max_length=20, choices=[
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
        ('USDT', 'Tether'),
        ('USDC', 'USD Coin'),
        ('BNB', 'Binance Coin'),
    ])
    crypto_amount = models.DecimalField(max_digits=18, decimal_places=8)
    wallet_address = models.CharField(max_length=200)
    transaction_hash = models.CharField(max_length=200, blank=True)
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=3)
    status = models.CharField(max_length=20, choices=CRYPTO_STATUS, default='pending')
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Crypto Payment - {self.cryptocurrency} - {self.crypto_amount}"
    
    def is_confirmed(self):
        return self.confirmations >= self.required_confirmations
