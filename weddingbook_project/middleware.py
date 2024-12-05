from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import JsonResponse

class InactivityTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                try:
                    # Ensure last_activity is a timezone-aware datetime object
                    last_activity_time = now().fromisoformat(last_activity).astimezone()
                except ValueError:
                    # If session data is corrupted or invalid
                    last_activity_time = now()

                # Check if the inactivity period exceeds 60 minutes
                if now() - last_activity_time > timedelta(minutes=60):
                    logout(request)
                    if request.is_ajax() or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'detail': 'Session has expired due to inactivity.'}, status=401)
                    return redirect('users:login')  # Adjust the redirect URL as needed

            # Update last_activity timestamp for the current request
            request.session['last_activity'] = now().isoformat()

        # Proceed with the response
        response = self.get_response(request)
        return response
