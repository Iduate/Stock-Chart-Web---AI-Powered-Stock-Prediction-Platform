from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('ws/notifications/', views.websocket_placeholder, name='websocket_placeholder'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]
