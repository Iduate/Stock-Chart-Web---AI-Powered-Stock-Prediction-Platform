from django.utils import translation
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
import re

class SubdomainLanguageMiddleware:
    """
    Middleware to handle language switching based on subdomain
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract subdomain from request
        host = request.get_host()
        subdomain = self.get_subdomain(host)
        
        # Check if subdomain corresponds to a supported language
        if subdomain and subdomain in settings.SUBDOMAIN_LANGUAGES:
            # Activate the language based on subdomain
            translation.activate(subdomain)
            request.LANGUAGE_CODE = subdomain
        else:
            # Use default language
            translation.activate(settings.DEFAULT_LANGUAGE)
            request.LANGUAGE_CODE = settings.DEFAULT_LANGUAGE
        
        response = self.get_response(request)
        translation.deactivate()
        
        return response
    
    def get_subdomain(self, host):
        """Extract subdomain from host"""
        if not host:
            return None
            
        # Remove port if present
        host = host.split(':')[0]
        
        # Split by dots and check if we have a subdomain
        parts = host.split('.')
        if len(parts) >= 3:
            # Return the first part as subdomain
            return parts[0]
        
        return None

class FreemiumAccessMiddleware:
    """
    Middleware to control access to premium content for free users
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that require premium access
        self.premium_urls = [
            '/charts/premium/',
            '/charts/board/',
            '/contests/',
            '/rankings/',
            '/api/premium/',
        ]
        
        # URLs that consume free visits
        self.visit_consuming_urls = [
            '/charts/view/',
            '/predictions/view/',
            '/board/view/',
        ]

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user is trying to access premium content
            current_path = request.path
            
            # Check for premium content access
            if any(url in current_path for url in self.premium_urls):
                if not request.user.can_access_premium_content():
                    # Redirect to payment page
                    return HttpResponseRedirect(reverse('payments:subscribe'))
            
            # Check for visit-consuming content
            if any(url in current_path for url in self.visit_consuming_urls):
                if request.user.user_type == 'free':
                    if request.user.free_visits_remaining <= 0:
                        # Redirect to payment page
                        return HttpResponseRedirect(reverse('payments:subscribe'))
                    else:
                        # Consume a free visit (will be handled in view)
                        pass
        
        response = self.get_response(request)
        return response

class MaintenanceModeMiddleware:
    """
    Middleware to handle maintenance mode
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.MAINTENANCE_MODE:
            # Allow admin users to access during maintenance
            if request.user.is_authenticated and request.user.is_staff:
                pass
            else:
                # Return maintenance page for regular users
                from django.template.response import TemplateResponse
                return TemplateResponse(request, 'maintenance.html', status=503)
        
        response = self.get_response(request)
        return response
