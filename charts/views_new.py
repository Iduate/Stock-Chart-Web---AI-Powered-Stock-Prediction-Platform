from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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

# API Views

@api_view(['GET'])
def markets_api(request):
    """API endpoint to get markets by type"""
    market_type = request.GET.get('type', 'stocks')
    
    markets = Market.objects.filter(market_type=market_type.upper())
    
    markets_data = []
    for market in markets:
        # Get latest stock data for current price
        latest_data = StockData.objects.filter(market=market).order_by('-timestamp').first()
        
        if latest_data:
            current_price = float(latest_data.close)
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

@api_view(['GET'])
def chart_data_api(request, symbol):
    """API endpoint to get chart data for a specific symbol"""
    timeframe = request.GET.get('timeframe', '1D')
    
    try:
        market = Market.objects.get(symbol=symbol.upper())
        
        # Get stock data based on timeframe
        if timeframe == '1D':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:24]
        elif timeframe == '1W':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:168]  # 7 days * 24 hours
        elif timeframe == '1M':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:720]  # 30 days * 24 hours
        elif timeframe == '3M':
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:2160]  # 90 days * 24 hours
        else:  # 1Y
            stock_data = StockData.objects.filter(market=market).order_by('-timestamp')[:8760]  # 365 days * 24 hours
        
        # Reverse to get chronological order
        stock_data = list(stock_data)[::-1]
        
        # Format data for TradingView
        candles = []
        volume = []
        
        for data in stock_data:
            timestamp = int(data.timestamp.timestamp())
            candles.append({
                'time': timestamp,
                'open': float(data.open),
                'high': float(data.high),
                'low': float(data.low),
                'close': float(data.close)
            })
            volume.append({
                'time': timestamp,
                'value': float(data.volume)
            })
        
        current_price = float(stock_data[-1].close) if stock_data else 0
        
        return JsonResponse({
            'symbol': symbol,
            'candles': candles,
            'volume': volume,
            'current_price': current_price
        })
        
    except Market.DoesNotExist:
        return JsonResponse({'error': 'Market not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prediction_api(request):
    """API endpoint to create a new prediction"""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        market_id = data.get('market_id')
        prediction_type = data.get('prediction_type')
        target_price = data.get('target_price')
        time_frame = data.get('time_frame')
        confidence = data.get('confidence', 5)
        reasoning = data.get('reasoning', '')
        
        market = Market.objects.get(id=market_id)
        
        prediction = ChartPrediction.objects.create(
            user=request.user,
            market=market,
            prediction_type=prediction_type,
            target_price=Decimal(str(target_price)),
            time_frame=time_frame,
            confidence_level=int(confidence),
            reasoning=reasoning,
            current_price=Decimal('100.00')  # Should get from latest market data
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

@api_view(['GET'])
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

@api_view(['GET'])
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

# Contest Views

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

@login_required
def join_contest(request, contest_id):
    """Join a contest"""
    contest = get_object_or_404(Contest, id=contest_id)
    
    # Check if user already joined
    # (This would typically be handled by a ContestParticipant model)
    
    return JsonResponse({'success': True, 'message': 'Joined contest successfully'})
