from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()

class SupportedCryptocurrency(models.Model):
    """Cryptocurrencies supported as collateral"""
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, unique=True)
    contract_address = models.CharField(max_length=100, blank=True)
    network = models.CharField(max_length=50, choices=[
        ('ethereum', 'Ethereum'),
        ('bitcoin', 'Bitcoin'),
        ('binance_smart_chain', 'Binance Smart Chain'),
        ('polygon', 'Polygon'),
        ('avalanche', 'Avalanche'),
        ('solana', 'Solana'),
    ])
    min_collateral_amount = models.DecimalField(max_digits=18, decimal_places=8)
    loan_to_value_ratio = models.FloatField(help_text="Maximum LTV ratio (e.g., 0.7 for 70%)")
    liquidation_threshold = models.FloatField(help_text="LTV ratio that triggers liquidation")
    is_active = models.BooleanField(default=True)
    current_price_usd = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    price_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
    class Meta:
        ordering = ['symbol']

class LoanProduct(models.Model):
    """Different loan products available"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    annual_interest_rate = models.FloatField(help_text="Annual interest rate as percentage")
    min_term_days = models.IntegerField()
    max_term_days = models.IntegerField()
    supported_cryptocurrencies = models.ManyToManyField(SupportedCryptocurrency)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class CryptoWallet(models.Model):
    """User crypto wallets for collateral deposits"""
    WALLET_STATUS = (
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('frozen', 'Frozen'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crypto_wallets')
    cryptocurrency = models.ForeignKey(SupportedCryptocurrency, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=100, unique=True)
    private_key_encrypted = models.TextField()  # Should be properly encrypted
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    status = models.CharField(max_length=20, choices=WALLET_STATUS, default='active')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'cryptocurrency')
    
    def __str__(self):
        return f"{self.user.email} - {self.cryptocurrency.symbol} wallet"

class LoanApplication(models.Model):
    """Loan applications from users"""
    APPLICATION_STATUS = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_applications')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested_term_days = models.IntegerField()
    collateral_cryptocurrency = models.ForeignKey(SupportedCryptocurrency, on_delete=models.CASCADE)
    collateral_amount = models.DecimalField(max_digits=18, decimal_places=8)
    collateral_value_usd = models.DecimalField(max_digits=12, decimal_places=2)
    loan_to_value_ratio = models.FloatField()
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    application_data = models.JSONField(default=dict)
    credit_score = models.IntegerField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_loan_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loan Application {self.id} - {self.user.email}"
    
    def calculate_ltv(self):
        """Calculate current loan-to-value ratio"""
        if self.collateral_value_usd > 0:
            return float(self.requested_amount / self.collateral_value_usd)
        return 0.0

class Loan(models.Model):
    """Active loans"""
    LOAN_STATUS = (
        ('active', 'Active'),
        ('paid_off', 'Paid Off'),
        ('defaulted', 'Defaulted'),
        ('liquidated', 'Liquidated'),
        ('suspended', 'Suspended'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.CASCADE)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.FloatField()
    term_days = models.IntegerField()
    collateral_amount = models.DecimalField(max_digits=18, decimal_places=8)
    collateral_cryptocurrency = models.ForeignKey(SupportedCryptocurrency, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=LOAN_STATUS, default='active')
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2)
    next_payment_due = models.DateTimeField()
    maturity_date = models.DateTimeField()
    smart_contract_address = models.CharField(max_length=100, blank=True)
    collateral_wallet = models.ForeignKey(CryptoWallet, on_delete=models.CASCADE)
    current_ltv_ratio = models.FloatField(default=0.0)
    liquidation_threshold = models.FloatField()
    warning_threshold = models.FloatField()
    auto_liquidation_enabled = models.BooleanField(default=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    paid_off_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Loan {self.id} - {self.user.email}"
    
    def calculate_total_interest(self):
        """Calculate total interest for the loan"""
        daily_rate = self.interest_rate / 365 / 100
        return self.principal_amount * Decimal(str(daily_rate)) * self.term_days
    
    def calculate_daily_interest(self):
        """Calculate daily interest amount"""
        daily_rate = self.interest_rate / 365 / 100
        return self.outstanding_balance * Decimal(str(daily_rate))
    
    def is_at_risk(self):
        """Check if loan is at risk of liquidation"""
        return self.current_ltv_ratio >= self.warning_threshold
    
    def should_liquidate(self):
        """Check if loan should be liquidated"""
        return self.current_ltv_ratio >= self.liquidation_threshold

class LoanPayment(models.Model):
    """Track loan payments"""
    PAYMENT_TYPE = (
        ('interest', 'Interest Payment'),
        ('principal', 'Principal Payment'),
        ('full_repayment', 'Full Repayment'),
        ('penalty', 'Penalty Payment'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_hash = models.CharField(max_length=100, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.id} - Loan {self.loan.id}"
    
    def is_overdue(self):
        from django.utils import timezone
        return timezone.now() > self.due_date and self.status == 'pending'

class CollateralTransaction(models.Model):
    """Track collateral deposits and withdrawals"""
    TRANSACTION_TYPE = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('liquidation', 'Liquidation'),
        ('transfer', 'Transfer'),
    )
    
    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='collateral_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    cryptocurrency = models.ForeignKey(SupportedCryptocurrency, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    value_usd_at_time = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_hash = models.CharField(max_length=100, unique=True)
    from_address = models.CharField(max_length=100, blank=True)
    to_address = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=6)
    gas_fee = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.cryptocurrency.symbol}"
    
    def is_confirmed(self):
        return self.confirmations >= self.required_confirmations

class LiquidationEvent(models.Model):
    """Track liquidation events"""
    LIQUIDATION_STATUS = (
        ('initiated', 'Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='liquidation_events')
    trigger_ltv_ratio = models.FloatField()
    collateral_price_at_trigger = models.DecimalField(max_digits=18, decimal_places=8)
    liquidated_amount = models.DecimalField(max_digits=18, decimal_places=8)
    liquidation_value_usd = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_debt = models.DecimalField(max_digits=12, decimal_places=2)
    excess_collateral = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    liquidation_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=LIQUIDATION_STATUS, default='initiated')
    liquidation_transaction_hash = models.CharField(max_length=100, blank=True)
    automated = models.BooleanField(default=True)
    liquidated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_liquidations')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Liquidation - Loan {self.loan.id} - {self.status}"

class LoanAlert(models.Model):
    """Alerts for loan status changes"""
    ALERT_TYPE = (
        ('payment_due', 'Payment Due'),
        ('payment_overdue', 'Payment Overdue'),
        ('ltv_warning', 'LTV Warning'),
        ('liquidation_warning', 'Liquidation Warning'),
        ('liquidation_executed', 'Liquidation Executed'),
        ('loan_paid_off', 'Loan Paid Off'),
    )
    
    ALERT_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('expired', 'Expired'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ])
    status = models.CharField(max_length=20, choices=ALERT_STATUS, default='pending')
    sent_via = models.JSONField(default=list)  # email, sms, push, etc.
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Alert - {self.alert_type} - Loan {self.loan.id}"

class SmartContractInteraction(models.Model):
    """Track smart contract interactions"""
    INTERACTION_TYPE = (
        ('deposit_collateral', 'Deposit Collateral'),
        ('withdraw_collateral', 'Withdraw Collateral'),
        ('liquidate', 'Liquidate'),
        ('repay_loan', 'Repay Loan'),
        ('update_oracle', 'Update Oracle'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='contract_interactions')
    interaction_type = models.CharField(max_length=30, choices=INTERACTION_TYPE)
    contract_address = models.CharField(max_length=100)
    function_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)
    transaction_hash = models.CharField(max_length=100, unique=True)
    gas_used = models.BigIntegerField()
    gas_price = models.BigIntegerField()
    success = models.BooleanField()
    error_message = models.TextField(blank=True)
    block_number = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contract interaction - {self.interaction_type} - {self.transaction_hash[:10]}..."
