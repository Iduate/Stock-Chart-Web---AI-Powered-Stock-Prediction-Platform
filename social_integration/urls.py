from django.urls import path
from . import views

app_name = 'social_integration'

urlpatterns = [
    path('connect/<str:platform>/', views.connect_social_account, name='connect_social_account'),
    path('disconnect/<str:platform>/', views.disconnect_social_account, name='disconnect_social_account'),
    path('post/', views.create_social_post, name='create_social_post'),
    path('campaigns/', views.campaigns_view, name='campaigns'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('api/social-accounts/', views.SocialAccountAPIView.as_view(), name='api_social_accounts'),
    path('api/auto-post/', views.AutoPostAPIView.as_view(), name='api_auto_post'),
]
