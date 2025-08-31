from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SocialAccount, SocialPost, AutoPostSettings

@login_required
def connect_social_account(request, platform):
    """Connect a social media account"""
    # This would integrate with OAuth providers
    messages.info(request, f'Connecting to {platform} is not yet implemented')
    return redirect('users:profile')

@login_required
def disconnect_social_account(request, platform):
    """Disconnect a social media account"""
    try:
        account = SocialAccount.objects.get(user=request.user, platform=platform)
        account.delete()
        messages.success(request, f'{platform} account disconnected successfully')
    except SocialAccount.DoesNotExist:
        messages.error(request, f'No {platform} account found')
    
    return redirect('users:profile')

@login_required
def create_social_post(request):
    """Create a social media post"""
    if request.method == 'POST':
        content = request.POST.get('content')
        platforms = request.POST.getlist('platforms')
        
        # Create post records
        for platform in platforms:
            try:
                account = SocialAccount.objects.get(user=request.user, platform=platform)
                SocialPost.objects.create(
                    social_account=account,
                    post_type='promotional',
                    content=content,
                )
            except SocialAccount.DoesNotExist:
                continue
        
        messages.success(request, 'Posts scheduled successfully')
        return redirect('social_integration:campaigns')
    
    return render(request, 'social_integration/create_post.html')

@login_required
def campaigns_view(request):
    """View social media campaigns"""
    posts = SocialPost.objects.filter(
        social_account__user=request.user
    ).order_by('-created_at')
    
    context = {
        'posts': posts,
    }
    
    return render(request, 'social_integration/campaigns.html', context)

@login_required
def analytics_view(request):
    """View social media analytics"""
    accounts = SocialAccount.objects.filter(user=request.user)
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'social_integration/analytics.html', context)

# API Views
class SocialAccountAPIView(generics.ListAPIView):
    """API for user's social accounts"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        accounts = SocialAccount.objects.filter(user=request.user)
        
        data = [{
            'platform': account.platform,
            'username': account.username,
            'is_active': account.is_active,
        } for account in accounts]
        
        return Response(data)

class AutoPostAPIView(generics.RetrieveUpdateAPIView):
    """API for auto-post settings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            settings = AutoPostSettings.objects.get(user=request.user)
            data = {
                'auto_post_predictions': settings.auto_post_predictions,
                'auto_post_achievements': settings.auto_post_achievements,
                'auto_post_contest_wins': settings.auto_post_contest_wins,
                'platforms_enabled': settings.platforms_enabled,
            }
        except AutoPostSettings.DoesNotExist:
            data = {
                'auto_post_predictions': False,
                'auto_post_achievements': False,
                'auto_post_contest_wins': False,
                'platforms_enabled': [],
            }
        
        return Response(data)
    
    def patch(self, request, *args, **kwargs):
        settings, created = AutoPostSettings.objects.get_or_create(user=request.user)
        
        for field in ['auto_post_predictions', 'auto_post_achievements', 'auto_post_contest_wins']:
            if field in request.data:
                setattr(settings, field, request.data[field])
        
        if 'platforms_enabled' in request.data:
            settings.platforms_enabled = request.data['platforms_enabled']
        
        settings.save()
        
        return Response({'success': True, 'message': 'Settings updated'})
