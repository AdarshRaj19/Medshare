from .models import UserProfile


class EnsureUserProfileMiddleware:
    """
    Ensure every authenticated non-superuser has a UserProfile.
    This avoids template/runtime errors when referencing `user.profile`.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            UserProfile.objects.get_or_create(user=request.user)
        return self.get_response(request)


class RequireLoginMiddleware:
    """Require login for protected URL prefixes.

    Exempt paths: /login/, /signup/, /admin/, /static/, /api/ and home/search pages remain public.
    """

    EXEMPT_PREFIXES = (
        '/login', '/signup', '/admin', '/static', '/media', '/api', '/about', '/contact', '/faq', '/', '/search', '/medicines-map'
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        # Only protect specific prefixes (donor/ngo/pickup-delivery)
        protect_prefixes = ('/donor/', '/ngo/', '/pickup-delivery/')

        if any(path.startswith(p) for p in protect_prefixes):
            if not request.user.is_authenticated:
                from django.shortcuts import redirect
                return redirect('login')

        return self.get_response(request)


