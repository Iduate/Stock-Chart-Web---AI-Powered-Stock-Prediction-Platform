from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from .models import Market, StockData, ChartPrediction, Contest
import json
import random
from datetime import datetime, timedelta
from decimal import Decimal

User = get_user_model()

def home_view(request):
    """Home page with trending predictions and top performers"""
    trending_predictions = ChartPrediction.objects.filter(
        is_public=True,
        status='pending'
    ).select_related('market', 'user').order_by('-views_count')[:5]
    
    top_performers = User.objects.filter(
        total_predictions__gt=0
    ).order_by('-total_accuracy_rate')[:5]
    
    current_contests = Contest.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )[:2]
    
    # Sample stats (in production, calculate from database)
    context = {
        'trending_predictions': trending_predictions,
        'top_performers': top_performers,
        'current_contests': current_contests,
        'total_users': User.objects.count(),
        'total_predictions': ChartPrediction.objects.count(),
        'total_rewards': '100,000+',  # Calculate from payments
        'accuracy_rate': '78%',  # Calculate average accuracy
    }
    
    return render(request, 'home.html', context)

def chart_board_view(request):
    """Chart board page with interactive charts"""
    return render(request, 'charts/chart_board.html')

def chart_detail_view(request, symbol):
    """Individual chart page for a specific market"""
    market = get_object_or_404(Market, symbol=symbol.upper())
    
    # Get recent stock data
    stock_data = StockData.objects.filter(
        market=market
    ).order_by('-timestamp')[:100]
    
    # Get recent predictions for this market
    recent_predictions = ChartPrediction.objects.filter(
        market=market,
        is_public=True
    ).select_related('user').order_by('-created_at')[:10]
    
    context = {
        'market': market,
        'stock_data': stock_data,
        'recent_predictions': recent_predictions,
    }
    
    return render(request, 'charts/chart_detail.html', context)

@login_required
def predictions_view(request):
    """User's predictions page"""
    user_predictions = ChartPrediction.objects.filter(
        user=request.user
    ).select_related('market').order_by('-created_at')
    
    # Calculate user stats
    total_predictions = user_predictions.count()
    correct_predictions = user_predictions.filter(status='correct').count()
    accuracy_rate = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    context = {
        'predictions': user_predictions,
        'total_predictions': total_predictions,
        'correct_predictions': correct_predictions,
        'accuracy_rate': round(accuracy_rate, 2),
    }
    
    return render(request, 'charts/predictions.html', context)

def rankings_view(request):
    """Global rankings page"""
    top_users = User.objects.filter(
        total_predictions__gt=0
    ).order_by('-total_accuracy_rate')[:50]
    
    context = {
        'top_users': top_users,
    }
    
    return render(request, 'charts/rankings.html', context)

def contests_view(request):
    """Contest listing page"""
    active_contests = Contest.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    )
    
    upcoming_contests = Contest.objects.filter(
        is_active=True,
        start_date__gt=timezone.now()
    )[:5]
    
    context = {
        'active_contests': active_contests,
        'upcoming_contests': upcoming_contests,
    }
    
    return render(request, 'charts/contests.html', context)

# API Views

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def markets_api(request):
    """API endpoint to get markets by type"""
    market_type = request.GET.get('type', 'stocks')
    
    markets = Market.objects.filter(market_type=market_type.upper())
    
    markets_data = []
    for market in markets:
        # Get latest stock data for current price
        latest_data = StockData.objects.filter(market=market).order_by('-timestamp').first()
        
        if latest_data:
            current_price = float(latest_data.close_price)
            # Calculate price change (simplified - in production, compare with previous day)
            price_change = random.uniform(-5, 5)  # Mock data
        else:
            current_price = random.uniform(10, 1000)  # Mock data
            price_change = random.uniform(-5, 5)
        
        markets_data.append({
            'id': market.id,
            'symbol': market.symbol,
            'name': market.name,
            'current_price': current_price,
            'price_change': price_change,
            'market_type': market.market_type
        })
    
    return JsonResponse({'markets': markets_data})

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def chart_data_api(request, symbol):
    """API endpoint to get chart data for a specific symbol"""
    timeframe = request.GET.get('timeframe', '1D')
    
    try:
        market = Market.objects.get(symbol=symbol.upper())
        
        # Get stock data based on timeframe
        if timeframe == '1D':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:24]
        elif timeframe == '1W':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:168]
        elif timeframe == '1M':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:720]
        elif timeframe == '3M':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:2160]
        else:  # 1Y
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:8760]
        
        # Reverse to get chronological order
        stock_data = list(stock_data)[::-1]
        
        # Format data for TradingView
        candles = []
        volume = []
        
        for data in stock_data:
            timestamp = int(data.timestamp.timestamp())
            candles.append({
                'time': timestamp,
                'open': float(data.open_price),
                'high': float(data.high_price),
                'low': float(data.low_price),
                'close': float(data.close_price)
            })
            volume.append({
                'time': timestamp,
                'value': float(data.volume)
            })
        
        current_price = float(stock_data[-1].close_price) if stock_data else 0
        
        return JsonResponse({
            'symbol': symbol,
            'candles': candles,
            'volume': volume,
            'current_price': current_price
        })
        
    except Market.DoesNotExist:
        return JsonResponse({'error': 'Market not found'}, status=404)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prediction_api(request):
    """API endpoint to create a new prediction"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        market_id = data.get('market')
        predicted_price = data.get('predicted_price')
        target_date = data.get('target_date')
        confidence_level = data.get('confidence_level', 50)
        notes = data.get('notes', '')
        is_public = data.get('is_public', 'on') == 'on'  # Handle checkbox
        
        # Validate required fields
        if not all([market_id, predicted_price, target_date]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            }, status=400)
        
        market = Market.objects.get(id=market_id)
        
        # Get current price from latest stock data or use a default
        latest_data = StockData.objects.filter(market=market).order_by('-timestamp').first()
        current_price = latest_data.close_price if latest_data else Decimal('100.00')
        
        # Parse target date
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        target_datetime = timezone.make_aware(datetime.combine(target_date_obj, datetime.min.time()))
        
        # Calculate duration in days
        duration_days = (target_date_obj - timezone.now().date()).days
        
        prediction = ChartPrediction.objects.create(
            user=request.user,
            market=market,
            target_date=target_datetime,
            current_price=current_price,
            predicted_price=Decimal(str(predicted_price)),
            duration_days=duration_days,
            confidence_level=int(confidence_level),
            notes=notes,
            is_public=is_public
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Prediction created successfully',
            'prediction_id': prediction.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def recent_predictions_api(request):
    """API endpoint to get recent predictions"""
    predictions = ChartPrediction.objects.all().select_related('market', 'user').order_by('-created_at')[:10]
    
    predictions_data = []
    for prediction in predictions:
        time_diff = timezone.now() - prediction.created_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}d ago"
        elif time_diff.seconds > 3600:
            time_ago = f"{time_diff.seconds // 3600}h ago"
        else:
            time_ago = f"{time_diff.seconds // 60}m ago"
        
        predictions_data.append({
            'id': prediction.id,
            'market_symbol': prediction.market.symbol,
            'prediction_type': prediction.prediction_type,
            'target_price': str(prediction.target_price),
            'status': prediction.status,
            'time_ago': time_ago,
            'user': prediction.user.username
        })
    
    return JsonResponse({'predictions': predictions_data})

@csrf_exempt
@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def prediction_detail_api(request, prediction_id):
    """API endpoint to get or delete a specific prediction"""
    try:
        prediction = ChartPrediction.objects.select_related('market', 'user').get(
            id=prediction_id,
            user=request.user
        )
        
        if request.method == 'GET':
            return JsonResponse({
                'id': str(prediction.id),
                'market': {
                    'symbol': prediction.market.symbol,
                    'name': prediction.market.name,
                    'market_type': prediction.market.get_market_type_display()
                },
                'current_price': str(prediction.current_price),
                'predicted_price': str(prediction.predicted_price),
                'actual_price': str(prediction.actual_price) if prediction.actual_price else None,
                'target_date': prediction.target_date.isoformat(),
                'confidence_level': prediction.confidence_level,
                'status': prediction.status,
                'notes': prediction.notes,
                'accuracy_percentage': prediction.accuracy_percentage,
                'created_at': prediction.created_at.isoformat()
            })
        
        elif request.method == 'DELETE':
            if prediction.status == 'pending':
                prediction.delete()
                return JsonResponse({'success': True, 'message': 'Prediction deleted successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Cannot delete completed prediction'})
                
    except ChartPrediction.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prediction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard_api(request):
    """API endpoint to get leaderboard"""
    top_users = User.objects.filter(
        total_predictions__gt=0
    ).order_by('-total_accuracy_rate')[:10]
    
    users_data = []
    for user in top_users:
        users_data.append({
            'username': user.username,
            'accuracy': round(user.total_accuracy_rate, 1) if user.total_accuracy_rate else 0,
            'total_predictions': user.total_predictions
        })
    
    return JsonResponse({'users': users_data})

# External Data Integration Functions

def fetch_real_time_data(symbol):
    """
    Fetch real-time data from external APIs
    This is a placeholder - integrate with actual APIs like Alpha Vantage, Yahoo Finance, etc.
    """
    # Example integration with Alpha Vantage (you'll need an API key)
    # import requests
    # API_KEY = 'your_alpha_vantage_api_key'
    # url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}'
    # response = requests.get(url)
    # return response.json()
    
    # For now, return mock data
    return {
        'symbol': symbol,
        'price': random.uniform(50, 500),
        'change': random.uniform(-10, 10),
        'volume': random.randint(100000, 1000000)
    }

def update_market_data():
    """
    Background task to update market data
    This should be called by a scheduler like Celery
    """
    markets = Market.objects.all()
    for market in markets:
        try:
            data = fetch_real_time_data(market.symbol)
            
            # Create new stock data entry
            StockData.objects.create(
                market=market,
                open=Decimal(str(data['price'])),
                high=Decimal(str(data['price'] * 1.02)),
                low=Decimal(str(data['price'] * 0.98)),
                close=Decimal(str(data['price'])),
                volume=data['volume'],
                timestamp=timezone.now()
            )
            
        except Exception as e:
            print(f"Error updating {market.symbol}: {e}")

@login_required
def join_contest(request, contest_id):
    """Join a contest"""
    contest = get_object_or_404(Contest, id=contest_id)
    
    # Check if user already joined
    # (This would typically be handled by a ContestParticipant model)
    
    return JsonResponse({'success': True, 'message': 'Joined contest successfully'})