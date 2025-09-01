"""
URL configuration for stockchart_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.http import JsonResponse

# Health check view for Railway
def health_check(request):
    return JsonResponse({"status": "healthy", "service": "Stock Chart Web"})

urlpatterns = [
    path('', health_check, name='health_check'),  # Health check for Railway
    path('admin/', admin.site.urls),
    path('notifications/', include('notifications.urls')),  # Move notifications to /notifications/
    path('i18n/', include('django.conf.urls.i18n')),  # Django's built-in language switching
]

# Internationalized URL patterns
urlpatterns += i18n_patterns(
    path('home/', include('charts.urls')),  # Changed from '' to 'home/'
    path('users/', include('users.urls')),
    path('api/charts/', include(('charts.urls', 'charts_api'), namespace='charts_api')),
    path('api/payments/', include('payments.urls')),
    path('api/social/', include('social_integration.urls')),
    path('api/loans/', include('loans.urls')),
    path('accounts/', include('allauth.urls')),
    prefix_default_language=False,  # Don't add language prefix for default language
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
