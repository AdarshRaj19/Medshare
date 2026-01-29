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


