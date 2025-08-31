from django.urls import path
from . import views, real_time_views

app_name = 'charts'

urlpatterns = [
    # Template views
    path('', views.home_view, name='home'),
    path('chart/<str:symbol>/', views.chart_detail_view, name='chart_detail'),
    path('predictions/', views.predictions_view, name='predictions'),
    path('chart-board/', views.chart_board_view, name='chart_board'),
    path('rankings/', views.rankings_view, name='rankings'),
    path('contests/', views.contests_view, name='contests'),
    
    # Real-time data views (using your API keys)
    path('dashboard/', real_time_views.market_dashboard, name='market_dashboard'),
    path('live-data/<str:symbol>/', real_time_views.get_market_data, name='get_market_data'),
    path('predict-live/', real_time_views.create_prediction, name='create_real_prediction'),
    path('my-predictions/', real_time_views.user_predictions, name='user_predictions'),
    path('test-api/', real_time_views.live_price_test, name='live_price_test'),
    
    # API endpoints (these will be available at /api/charts/ when included with namespace)
    path('markets/', views.markets_api, name='api_markets'),
    path('data/<str:symbol>/', views.chart_data_api, name='api_chart_data'),
    path('predictions/create/', views.create_prediction_api, name='api_create_prediction'),
    path('predictions/<uuid:prediction_id>/', views.prediction_detail_api, name='api_prediction_detail'),
    path('predictions/recent/', views.recent_predictions_api, name='api_recent_predictions'),
    path('leaderboard/', views.leaderboard_api, name='api_leaderboard'),
]
