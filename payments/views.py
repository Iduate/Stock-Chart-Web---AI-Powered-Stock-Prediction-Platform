from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SubscriptionPlan, Payment, Subscription
import json

def subscription_plans_view(request):
    """Display available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'payments/subscription_plans.html', context)

@login_required
def subscribe_view(request):
    """Handle subscription process"""
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        payment_method = request.POST.get('payment_method')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                subscription_plan=plan,
                amount=plan.price,
                payment_method=payment_method,
                transaction_id=f"TXN-{request.user.id}-{plan.id}",
            )
            
            messages.success(request, 'Subscription created successfully!')
            return redirect('payments:payment_success')
            
        except Exception as e:
            messages.error(request, f'Subscription failed: {str(e)}')
    
    return redirect('payments:subscription_plans')

def payment_success_view(request):
    """Payment success page"""
    return render(request, 'payments/payment_success.html')

def payment_cancel_view(request):
    """Payment cancellation page"""
    return render(request, 'payments/payment_cancel.html')

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    return HttpResponse(status=200)

@csrf_exempt
def paypal_webhook(request):
    """Handle PayPal webhooks"""
    return HttpResponse(status=200)

# API Views
class CreatePaymentIntentAPIView(generics.CreateAPIView):
    """Create payment intent for Stripe"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            amount = request.data.get('amount')
            currency = request.data.get('currency', 'USD')
            
            # Here you would integrate with Stripe
            # For now, return mock response
            
            return Response({
                'client_secret': 'pi_mock_client_secret',
                'amount': amount,
                'currency': currency,
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SubscriptionStatusAPIView(generics.RetrieveAPIView):
    """Get user's subscription status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active'
        ).first()
        
        data = {
            'is_premium': user.is_premium(),
            'user_type': user.user_type,
            'free_visits_remaining': user.free_visits_remaining,
            'subscription': None
        }
        
        if active_subscription:
            data['subscription'] = {
                'plan_name': active_subscription.plan.name,
                'end_date': active_subscription.end_date.isoformat(),
                'auto_renewal': active_subscription.auto_renewal,
            }
        
        return Response(data)
