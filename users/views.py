from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import User, UserProfile, ReferralSystem
import uuid
import json

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        # Check if this is an AJAX request by looking for the X-Requested-With header
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Handle different request types
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        email = data.get('email')
        password1 = data.get('password1')
        password2 = data.get('password2')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Generate unique username from email
        base_username = email.split('@')[0] if email else ''
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Basic validation
        if not email:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Email is required'})
            messages.error(request, 'Email is required')
            return render(request, 'users/register.html')
            
        if not password1:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Password is required'})
            messages.error(request, 'Password is required')
            return render(request, 'users/register.html')
            
        if len(password1) < 8:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters long'})
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'users/register.html')
            
        if password1 != password2:
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Passwords do not match'})
            messages.error(request, 'Passwords do not match')
            return render(request, 'users/register.html')
        
        if User.objects.filter(email=email).exists():
            if is_ajax:
                return JsonResponse({'success': False, 'message': 'Email already exists'})
            messages.error(request, 'Email already exists')
            return render(request, 'users/register.html')
        
        try:
            # Generate unique referral code
            referral_code = str(uuid.uuid4())[:8].upper()
            while User.objects.filter(referral_code=referral_code).exists():
                referral_code = str(uuid.uuid4())[:8].upper()
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                referral_code=referral_code
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Check for referral
            referral_code_used = data.get('referral_code')
            if referral_code_used:
                try:
                    referrer = User.objects.get(referral_code=referral_code_used)
                    ReferralSystem.objects.create(
                        referrer=referrer,
                        referred_user=user
                    )
                    if is_ajax:
                        pass  # Handle in response
                    else:
                        messages.success(request, f'Welcome! You were referred by {referrer.email}')
                except User.DoesNotExist:
                    pass
            
            login(request, user)
            
            if is_ajax:
                return JsonResponse({
                    'success': True, 
                    'message': 'Registration successful!',
                    'redirect_url': '/charts/'
                })
            else:
                messages.success(request, 'Registration successful! Welcome to Stock Chart Web!')
                return redirect('charts:home')
            
        except Exception as e:
            if is_ajax:
                return JsonResponse({'success': False, 'message': f'Registration failed: {str(e)}'})
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'users/register.html')

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        # Handle AJAX requests
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        email = data.get('email')
        password = data.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', '/charts/')
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful!',
                    'redirect_url': next_url
                })
            else:
                messages.success(request, 'Login successful!')
                return redirect(next_url)
        else:
            if request.content_type == 'application/json':
                return JsonResponse({'success': False, 'message': 'Invalid email or password'})
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('charts:home')

def password_reset_view(request):
    """Password reset view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Here you would typically send a password reset email
            # For now, just show a success message
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('users:login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'users/password_reset.html')

@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        # Update profile
        user = request.user
        profile = user.profile
        
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone_number = request.POST.get('phone_number', '')
        user.country = request.POST.get('country', '')
        user.preferred_language = request.POST.get('preferred_language', 'en')
        
        profile.bio = request.POST.get('bio', '')
        profile.website = request.POST.get('website', '')
        profile.trading_experience = request.POST.get('trading_experience', 'beginner')
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        user.save()
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    
    # Get user statistics
    from charts.models import ChartPrediction
    from payments.models import Subscription
    
    user_predictions = ChartPrediction.objects.filter(user=request.user)
    total_predictions = user_predictions.count()
    completed_predictions = user_predictions.filter(status='completed').count()
    pending_predictions = user_predictions.filter(status='pending').count()
    
    # Get active subscription
    active_subscription = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).first()
    
    # Get referrals
    referrals = ReferralSystem.objects.filter(referrer=request.user)
    
    context = {
        'total_predictions': total_predictions,
        'completed_predictions': completed_predictions,
        'pending_predictions': pending_predictions,
        'active_subscription': active_subscription,
        'referrals': referrals,
        'referral_count': referrals.count(),
        'total_earnings': sum(r.commission_earned for r in referrals),
    }
    
    return render(request, 'users/profile.html', context)

# API Views
class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """API endpoint for user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        
        data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'free_visits_remaining': user.free_visits_remaining,
            'total_accuracy_rate': user.total_accuracy_rate,
            'total_predictions': user.total_predictions,
            'is_premium': user.is_premium(),
            'referral_code': user.referral_code,
            'profile': {
                'bio': profile.bio,
                'website': profile.website,
                'trading_experience': profile.trading_experience,
                'favorite_markets': profile.favorite_markets,
            }
        }
        
        return Response(data)
    
    def patch(self, request, *args, **kwargs):
        user = request.user
        profile = user.profile
        
        # Update user fields
        for field in ['first_name', 'last_name', 'phone_number', 'country', 'preferred_language']:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        # Update profile fields
        for field in ['bio', 'website', 'trading_experience']:
            if field in request.data:
                setattr(profile, field, request.data[field])
        
        if 'favorite_markets' in request.data:
            profile.favorite_markets = request.data['favorite_markets']
        
        user.save()
        profile.save()
        
        return Response({'success': True, 'message': 'Profile updated successfully'})
