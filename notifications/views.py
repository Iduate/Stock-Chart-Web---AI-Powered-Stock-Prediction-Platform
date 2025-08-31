from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


@csrf_exempt 
@require_http_methods(["GET"])
def websocket_placeholder(request):
    """Placeholder for WebSocket endpoint until we implement real WebSockets"""
    return JsonResponse({
        'status': 'connected',
        'message': 'WebSocket not implemented yet',
        'notifications': []
    })


@csrf_exempt
def notifications_api(request):
    """API endpoint for getting user notifications"""
    if request.method == 'GET':
        # Mock notifications data
        notifications = [
            {
                'id': 1,
                'type': 'prediction_result',
                'title': 'Prediction Result',
                'message': 'Your BTC prediction was successful!',
                'timestamp': '2025-08-30T10:00:00Z',
                'read': False
            },
            {
                'id': 2,
                'type': 'market_alert',
                'title': 'Market Alert',
                'message': 'AAPL reached your target price of $180',
                'timestamp': '2025-08-30T09:30:00Z',
                'read': True
            }
        ]
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'unread_count': len([n for n in notifications if not n['read']])
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
