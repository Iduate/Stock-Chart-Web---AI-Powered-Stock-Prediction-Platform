from celery import shared_task
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_referral_payouts():
    """Process pending referral payouts"""
    try:
        from users.models import ReferralSystem
        from users.models import UserSubscriptionHistory
        
        # Get unpaid referrals where referred user has made a payment
        unpaid_referrals = ReferralSystem.objects.filter(
            commission_paid=False,
            referred_user__subscriptionhistory__is_active=True
        ).distinct()
        
        for referral in unpaid_referrals:
            # Calculate commission based on referred user's payments
            from django.db.models import Sum
            total_payments = UserSubscriptionHistory.objects.filter(
                user=referral.referred_user,
                is_active=True
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            
            if total_payments >= Decimal(str(settings.MIN_PAYOUT_AMOUNT)):
                commission = total_payments * Decimal(str(settings.REFERRAL_COMMISSION_RATE))
                
                # Update referral record
                referral.commission_earned = commission
                referral.commission_paid = True
                referral.save()
                
                # Update referrer's earnings
                referrer = referral.referrer
                referrer.earnings_from_referrals += commission
                referrer.save()
                
                logger.info(f"Processed referral payout of ${commission} for {referrer.email}")
        
        return f"Processed {unpaid_referrals.count()} referral payouts"
    except Exception as e:
        logger.error(f"Error processing referral payouts: {str(e)}")
        return f"Error processing referral payouts: {str(e)}"

@shared_task
def cleanup_expired_coupons():
    """Remove expired and used coupons"""
    try:
        from users.models import Coupon
        
        expired_coupons = Coupon.objects.filter(
            expiry_date__lt=timezone.now()
        )
        
        expired_count = expired_coupons.count()
        expired_coupons.delete()
        
        logger.info(f"Cleaned up {expired_count} expired coupons")
        return f"Cleaned up {expired_count} expired coupons"
    except Exception as e:
        logger.error(f"Error cleaning up expired coupons: {str(e)}")
        return f"Error cleaning up expired coupons: {str(e)}"

@shared_task
def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    try:
        from django.contrib.auth import get_user_model
        import string
        import random
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        if not user.referral_code:
            # Generate unique referral code
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not User.objects.filter(referral_code=code).exists():
                    user.referral_code = code
                    user.save()
                    break
            
            logger.info(f"Generated referral code {code} for {user.email}")
        
        return f"Referral code generated for {user.email}"
    except Exception as e:
        logger.error(f"Error generating referral code: {str(e)}")
        return f"Error generating referral code: {str(e)}"

@shared_task
def create_social_promotion_coupon(promotion_id):
    """Create coupon for verified social media promotion"""
    try:
        from users.models import SocialPromotion, Coupon
        
        promotion = SocialPromotion.objects.get(id=promotion_id)
        
        if promotion.verification_status == 'verified' and not promotion.reward_given:
            # Create coupon
            coupon = Coupon.objects.create(
                code=Coupon.generate_code(),
                coupon_type='free_days',
                value=Decimal(str(settings.SNS_PROMOTION_COUPON_DAYS)),
                max_uses=1,
                expiry_date=timezone.now() + timezone.timedelta(days=settings.COUPON_EXPIRY_DAYS),
                created_by=promotion.user
            )
            
            promotion.reward_coupon = coupon
            promotion.reward_given = True
            promotion.save()
            
            # Send notification to user
            from notifications.tasks import send_coupon_notification
            send_coupon_notification.delay(promotion.user.id, coupon.id)
            
            logger.info(f"Created coupon {coupon.code} for social promotion {promotion_id}")
        
        return f"Coupon created for promotion {promotion_id}"
    except Exception as e:
        logger.error(f"Error creating promotion coupon: {str(e)}")
        return f"Error creating promotion coupon: {str(e)}"

@shared_task 
def update_user_accuracy_stats():
    """Update user accuracy statistics"""
    try:
        from django.contrib.auth import get_user_model
        from charts.models import ChartPrediction
        from django.db.models import Avg, Count
        
        User = get_user_model()
        
        users_with_predictions = User.objects.filter(
            predictions__status='completed'
        ).distinct()
        
        for user in users_with_predictions:
            stats = ChartPrediction.objects.filter(
                user=user,
                status='completed',
                accuracy_percentage__isnull=False
            ).aggregate(
                avg_accuracy=Avg('accuracy_percentage'),
                total_predictions=Count('id')
            )
            
            user.total_accuracy_rate = stats['avg_accuracy'] or 0.0
            user.total_predictions = stats['total_predictions'] or 0
            user.save()
        
        logger.info(f"Updated accuracy stats for {users_with_predictions.count()} users")
        return f"Updated accuracy stats for {users_with_predictions.count()} users"
    except Exception as e:
        logger.error(f"Error updating user accuracy stats: {str(e)}")
        return f"Error updating user accuracy stats: {str(e)}"
