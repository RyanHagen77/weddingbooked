from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth import logout
from django.http import JsonResponse


class InactivityTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                # Convert last_activity to a timezone-aware datetime object
                last_activity_time = now().fromisoformat(last_activity)
                # Check if the inactivity period exceeds 60 minutes
                if now() - last_activity_time > timedelta(minutes=60):
                    logout(request)
                    return JsonResponse({'detail': 'Session has expired due to inactivity.'}, status=401)
            # Update last_activity timestamp
            request.session['last_activity'] = now().isoformat()

        response = self.get_response(request)
        return response
