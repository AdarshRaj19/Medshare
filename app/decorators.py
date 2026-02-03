from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """Decorator to require a user to have one of the allowed roles in UserProfile.

    Usage: @role_required('donor') or @role_required('ngo','admin')
    Superusers are always allowed.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect('login')
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                role = user.profile.role
            except Exception:
                messages.error(request, 'Profile required to access this page.')
                return redirect('home')

            if role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, 'You do not have permission to view this page.')
            return redirect('home')

        return _wrapped
    return decorator
