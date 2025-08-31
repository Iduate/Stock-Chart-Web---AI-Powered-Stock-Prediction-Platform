from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class SocialAccount(models.Model):
    """Store social media account tokens for auto-posting"""
    PLATFORM_CHOICES = (
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter/X'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_user_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'platform', 'platform_user_id')
    
    def __str__(self):
        return f"{self.user.email} - {self.platform} ({self.username})"

class SocialPost(models.Model):
    """Track social media posts made through the platform"""
    POST_STATUS = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('deleted', 'Deleted'),
    )
    
    POST_TYPES = (
        ('chart_prediction', 'Chart Prediction'),
        ('contest_announcement', 'Contest Announcement'),
        ('user_achievement', 'User Achievement'),
        ('platform_update', 'Platform Update'),
        ('promotional', 'Promotional'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    social_account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=30, choices=POST_TYPES)
    content = models.TextField()
    image_url = models.URLField(blank=True)
    hashtags = models.JSONField(default=list)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=POST_STATUS, default='draft')
    platform_post_id = models.CharField(max_length=100, blank=True)
    platform_url = models.URLField(blank=True)
    engagement_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.social_account.platform} post - {self.post_type}"
    
    class Meta:
        ordering = ['-created_at']

class AutoPostSettings(models.Model):
    """User settings for automatic social media posting"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auto_post_settings')
    auto_post_predictions = models.BooleanField(default=False)
    auto_post_achievements = models.BooleanField(default=False)
    auto_post_contest_wins = models.BooleanField(default=False)
    auto_post_accuracy_milestones = models.BooleanField(default=False)
    min_accuracy_for_auto_post = models.IntegerField(default=70)
    platforms_enabled = models.JSONField(default=list)
    custom_hashtags = models.JSONField(default=list)
    post_template = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Auto-post settings for {self.user.email}"

class SocialEngagement(models.Model):
    """Track engagement metrics from social media posts"""
    post = models.ForeignKey(SocialPost, on_delete=models.CASCADE, related_name='engagement_metrics')
    metric_type = models.CharField(max_length=20, choices=[
        ('likes', 'Likes'),
        ('shares', 'Shares'),
        ('comments', 'Comments'),
        ('views', 'Views'),
        ('clicks', 'Clicks'),
        ('followers_gained', 'Followers Gained'),
    ])
    count = models.IntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'metric_type', 'recorded_at')
    
    def __str__(self):
        return f"{self.post.id} - {self.metric_type}: {self.count}"

class ViralContent(models.Model):
    """Track viral content and successful posts"""
    post = models.OneToOneField(SocialPost, on_delete=models.CASCADE, related_name='viral_metrics')
    total_engagement = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    click_through_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    referral_traffic = models.IntegerField(default=0)
    new_signups_from_post = models.IntegerField(default=0)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_viral = models.BooleanField(default=False)
    viral_threshold_reached_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Viral metrics for post {self.post.id}"

class SocialCampaign(models.Model):
    """Manage social media campaigns"""
    CAMPAIGN_STATUS = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    campaign_type = models.CharField(max_length=30, choices=[
        ('user_acquisition', 'User Acquisition'),
        ('engagement', 'Engagement'),
        ('retention', 'Retention'),
        ('contest_promotion', 'Contest Promotion'),
        ('product_launch', 'Product Launch'),
    ])
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    target_platforms = models.JSONField(default=list)
    target_audience = models.JSONField(default=dict)
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    posts = models.ManyToManyField(SocialPost, blank=True, related_name='campaigns')
    success_metrics = models.JSONField(default=dict)
    actual_metrics = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class InfluencerPartnership(models.Model):
    """Manage influencer partnerships and collaborations"""
    PARTNERSHIP_STATUS = (
        ('proposed', 'Proposed'),
        ('negotiating', 'Negotiating'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    influencer_name = models.CharField(max_length=100)
    platform = models.CharField(max_length=20, choices=SocialAccount.PLATFORM_CHOICES)
    handle = models.CharField(max_length=100)
    follower_count = models.IntegerField()
    engagement_rate = models.FloatField()
    partnership_type = models.CharField(max_length=30, choices=[
        ('sponsored_post', 'Sponsored Post'),
        ('product_review', 'Product Review'),
        ('contest_collaboration', 'Contest Collaboration'),
        ('brand_ambassador', 'Brand Ambassador'),
    ])
    status = models.CharField(max_length=20, choices=PARTNERSHIP_STATUS, default='proposed')
    compensation_amount = models.DecimalField(max_digits=10, decimal_places=2)
    compensation_type = models.CharField(max_length=20, choices=[
        ('monetary', 'Monetary'),
        ('product', 'Product/Service'),
        ('revenue_share', 'Revenue Share'),
    ])
    deliverables = models.TextField()
    contract_terms = models.TextField()
    performance_metrics = models.JSONField(default=dict)
    actual_performance = models.JSONField(default=dict)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.influencer_name} - {self.platform} partnership"

class SocialAnalytics(models.Model):
    """Daily social media analytics aggregation"""
    date = models.DateField()
    platform = models.CharField(max_length=20, choices=SocialAccount.PLATFORM_CHOICES)
    total_posts = models.IntegerField(default=0)
    total_engagement = models.IntegerField(default=0)
    total_reach = models.IntegerField(default=0)
    total_impressions = models.IntegerField(default=0)
    new_followers = models.IntegerField(default=0)
    website_clicks = models.IntegerField(default=0)
    new_signups = models.IntegerField(default=0)
    revenue_attributed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    top_performing_post = models.ForeignKey(SocialPost, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('date', 'platform')
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.platform} analytics - {self.date}"
