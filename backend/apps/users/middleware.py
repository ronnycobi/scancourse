"""
Set the active language from authenticated user's preferred_language.
Falls back to Accept-Language header for anonymous users.
"""
from django.utils import translation


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            lang = getattr(request.user, 'preferred_language', None)
            if lang:
                translation.activate(lang)
                request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response
