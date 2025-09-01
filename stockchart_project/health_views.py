from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint for Railway deployment."""
    return JsonResponse({"status": "ok"}, status=200)
