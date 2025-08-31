from django.shortcuts import redirect
from django.utils import translation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json


@csrf_exempt
@require_http_methods(["POST"])
def set_language(request):
    """Set user's preferred language"""
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        language = data.get('language', 'en')
        
        # Validate language code
        supported_languages = ['en', 'ko', 'ja', 'zh']
        if language not in supported_languages:
            language = 'en'
        
        # Set language in session
        request.session['django_language'] = language
        translation.activate(language)
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True, 
                'language': language,
                'message': f'Language changed to {language.upper()}'
            })
        
        # For regular form submissions, redirect back
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', '/'))
        response = redirect(next_url)
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
