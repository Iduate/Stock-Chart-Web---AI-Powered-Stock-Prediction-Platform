from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('subscription-plans/', views.subscription_plans_view, name='subscription_plans'),
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-cancel/', views.payment_cancel_view, name='payment_cancel'),
    path('api/create-payment-intent/', views.CreatePaymentIntentAPIView.as_view(), name='api_create_payment_intent'),
    path('api/subscription-status/', views.SubscriptionStatusAPIView.as_view(), name='api_subscription_status'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('webhook/paypal/', views.paypal_webhook, name='paypal_webhook'),
]
