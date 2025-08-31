from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from charts.models import Market, StockData, ChartPrediction
from charts.market_api import StockDataAPI
from django.utils import timezone
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

def market_dashboard(request):
    """Dashboard showing all available markets with real-time data"""
    markets = Market.objects.filter(is_active=True)[:20]  # Limit to 20 for performance
    
    context = {
        'markets': markets,
        'total_markets': Market.objects.filter(is_active=True).count(),
    }
    return render(request, 'charts/market_dashboard.html', context)

@cache_page(60)  # Cache for 1 minute
def get_market_data(request, symbol):
    """API endpoint to get market data for a specific symbol"""
    try:
        market = get_object_or_404(Market, symbol=symbol, is_active=True)
        
        # Get recent stock data from database
        recent_data = StockData.objects.filter(
            market=market
        ).order_by('-timestamp')[:30]
        
        data_points = []
        for stock_data in recent_data:
            data_points.append({
                'timestamp': stock_data.timestamp.isoformat(),
                'open': float(stock_data.open_price),
                'high': float(stock_data.high_price),
                'low': float(stock_data.low_price),
                'close': float(stock_data.close_price),
                'volume': stock_data.volume,
            })
        
        # Get current price using real API
        api = StockDataAPI()
        current_price = api.get_current_price(market.api_symbol, market.market_type)
        
        response_data = {
            'symbol': market.symbol,
            'name': market.name,
            'market_type': market.market_type,
            'current_price': float(current_price) if current_price else None,
            'data': data_points,
            'last_updated': timezone.now().isoformat(),
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_prediction(request):
    """Create a new prediction using real market data"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            predicted_price = Decimal(str(data.get('predicted_price')))
            target_date = timezone.datetime.fromisoformat(data.get('target_date'))
            confidence_level = int(data.get('confidence_level', 50))
            notes = data.get('notes', '')
            
            market = get_object_or_404(Market, symbol=symbol, is_active=True)
            
            # Get current real price
            api = StockDataAPI()
            current_price = api.get_current_price(market.api_symbol, market.market_type)
            
            if not current_price:
                return JsonResponse({'error': 'Unable to get current price'}, status=400)
            
            # Check if user can make predictions
            if request.user.user_type == 'free' and request.user.free_visits_remaining <= 0:
                return JsonResponse({'error': 'Free visits exhausted. Please upgrade.'}, status=403)
            
            # Create prediction
            prediction = ChartPrediction.objects.create(
                user=request.user,
                market=market,
                target_date=target_date,
                current_price=current_price,
                predicted_price=predicted_price,
                duration_days=(target_date.date() - timezone.now().date()).days,
                confidence_level=confidence_level,
                notes=notes,
                is_public=True
            )
            
            # Consume free visit if free user
            if request.user.user_type == 'free':
                request.user.consume_free_visit()
            
            return JsonResponse({
                'success': True,
                'prediction_id': str(prediction.id),
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'message': 'Prediction created successfully!'
            })
            
        except Exception as e:
            logger.error(f"Error creating prediction: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show prediction form
    markets = Market.objects.filter(is_active=True)
    return render(request, 'charts/create_prediction.html', {'markets': markets})

def live_price_test(request):
    """Test page to verify API integration"""
    api = StockDataAPI()
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    results = {}
    
    for symbol in test_symbols:
        try:
            # Test current price
            current_price = api.get_current_price(symbol)
            
            # Test historical data
            historical_data = api.get_stock_data(symbol, 'us_stock', period='5d')
            
            results[symbol] = {
                'current_price': float(current_price) if current_price else None,
                'historical_count': len(historical_data) if historical_data else 0,
                'status': 'success' if current_price else 'failed'
            }
            
        except Exception as e:
            results[symbol] = {
                'error': str(e),
                'status': 'error'
            }
    
    return JsonResponse({
        'api_test_results': results,
        'alpha_vantage_configured': bool(api.alpha_vantage_key),
        'finnhub_configured': bool(api.finnhub_key),
        'twelve_data_configured': bool(api.twelve_data_key),
        'timestamp': timezone.now().isoformat()
    })

@login_required 
def user_predictions(request):
    """Show user's predictions with real accuracy calculations"""
    predictions = ChartPrediction.objects.filter(
        user=request.user
    ).select_related('market').order_by('-created_at')
    
    # Update accuracy for completed predictions
    api = StockDataAPI()
    for prediction in predictions:
        if (prediction.status == 'pending' and 
            prediction.target_date <= timezone.now()):
            
            # Get actual current price
            actual_price = api.get_current_price(
                prediction.market.api_symbol, 
                prediction.market.market_type
            )
            
            if actual_price:
                prediction.actual_price = actual_price
                prediction.calculate_accuracy()
                prediction.status = 'completed'
                prediction.save()
                
                # Update user's overall accuracy
                request.user.update_accuracy_rate(prediction.accuracy_percentage)
    
    context = {
        'predictions': predictions,
        'user_stats': {
            'total_predictions': request.user.total_predictions,
            'accuracy_rate': round(request.user.total_accuracy_rate, 2),
            'free_visits_remaining': request.user.free_visits_remaining,
        }
    }
    
    return render(request, 'charts/user_predictions.html', context)
