from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_market_data():
    """Update market data for all active markets"""
    try:
        from charts.market_api import MarketDataUpdater
        updater = MarketDataUpdater()
        updater.update_all_markets()
        logger.info("Market data updated successfully")
        return "Market data updated successfully"
    except Exception as e:
        logger.error(f"Error updating market data: {str(e)}")
        return f"Error updating market data: {str(e)}"

@shared_task
def check_prediction_accuracy():
    """Check and update accuracy for due predictions"""
    try:
        from charts.market_api import MarketDataUpdater
        updater = MarketDataUpdater()
        updater.update_predictions_accuracy()
        logger.info("Prediction accuracy updated successfully")
        return "Prediction accuracy updated successfully"
    except Exception as e:
        logger.error(f"Error updating prediction accuracy: {str(e)}")
        return f"Error updating prediction accuracy: {str(e)}"

@shared_task
def send_prediction_reminder(prediction_id):
    """Send reminder email when prediction target date is approaching"""
    try:
        from charts.models import ChartPrediction
        
        prediction = ChartPrediction.objects.get(id=prediction_id)
        
        if prediction.status == 'pending':
            subject = f"Your {prediction.market.symbol} prediction is due soon!"
            message = f"""
            Hi {prediction.user.username},
            
            Your prediction for {prediction.market.symbol} is due on {prediction.target_date.strftime('%Y-%m-%d')}.
            
            Current price: ${prediction.current_price}
            Your predicted price: ${prediction.predicted_price}
            
            We'll automatically check the accuracy when the target date arrives.
            
            Best regards,
            Stock Chart Prediction Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [prediction.user.email],
                fail_silently=False,
            )
            
            logger.info(f"Reminder email sent for prediction {prediction_id}")
        
        return f"Reminder sent for prediction {prediction_id}"
    except Exception as e:
        logger.error(f"Error sending prediction reminder: {str(e)}")
        return f"Error sending prediction reminder: {str(e)}"

@shared_task
def calculate_contest_rankings():
    """Calculate and update contest rankings"""
    try:
        from charts.models import Contest, ContestParticipation
        
        active_contests = Contest.objects.filter(
            is_active=True,
            end_date__gte=timezone.now()
        )
        
        for contest in active_contests:
            participants = ContestParticipation.objects.filter(
                contest=contest,
                prediction__status='completed'
            ).order_by('-final_accuracy')
            
            for rank, participant in enumerate(participants, 1):
                participant.rank = rank
                participant.save()
        
        logger.info("Contest rankings updated successfully")
        return "Contest rankings updated successfully"
    except Exception as e:
        logger.error(f"Error updating contest rankings: {str(e)}")
        return f"Error updating contest rankings: {str(e)}"
