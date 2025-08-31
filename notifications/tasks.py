from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_pending_notifications():
    """Send pending email notifications"""
    try:
        from notifications.models import Notification
        
        pending_notifications = Notification.objects.filter(
            is_sent=False,
            notification_type='email',
            scheduled_at__lte=timezone.now()
        )
        
        for notification in pending_notifications:
            try:
                send_mail(
                    notification.title,
                    notification.message,
                    settings.DEFAULT_FROM_EMAIL,
                    [notification.user.email],
                    fail_silently=False,
                )
                
                notification.is_sent = True
                notification.sent_at = timezone.now()
                notification.save()
                
                logger.info(f"Notification sent to {notification.user.email}")
            except Exception as e:
                logger.error(f"Error sending notification to {notification.user.email}: {str(e)}")
        
        return f"Processed {pending_notifications.count()} notifications"
    except Exception as e:
        logger.error(f"Error processing notifications: {str(e)}")
        return f"Error processing notifications: {str(e)}"

@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new users"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to Stock Chart Prediction Platform!"
        message = f"""
        Hi {user.username or user.email},
        
        Welcome to our Stock Chart Prediction Platform!
        
        You now have access to:
        - Real-time stock charts for multiple markets
        - AI-powered prediction tools
        - Social trading community
        - Contest participation
        
        As a new user, you have {user.free_visits_remaining} free visits to explore premium features.
        
        Get started by making your first prediction!
        
        Best regards,
        Stock Chart Prediction Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return f"Welcome email sent to {user.email}"
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return f"Error sending welcome email: {str(e)}"

@shared_task
def send_subscription_reminder(user_id):
    """Send subscription reminder to users with low free visits"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = User.objects.get(id=user_id)
        
        if user.user_type == 'free' and user.free_visits_remaining <= 1:
            subject = "Your free visits are running low!"
            message = f"""
            Hi {user.username or user.email},
            
            You have {user.free_visits_remaining} free visit(s) remaining.
            
            Upgrade to Premium to get:
            - Unlimited chart views
            - Advanced prediction tools
            - Contest participation
            - Detailed analytics
            
            Upgrade now and continue your trading journey!
            
            Best regards,
            Stock Chart Prediction Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f"Subscription reminder sent to {user.email}")
        
        return f"Subscription reminder processed for {user.email}"
    except Exception as e:
        logger.error(f"Error sending subscription reminder: {str(e)}")
        return f"Error sending subscription reminder: {str(e)}"
