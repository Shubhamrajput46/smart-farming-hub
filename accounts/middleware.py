import time

from django.conf import settings
from django.contrib.auth import logout
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.urls import reverse

from .models import FarmerProfile


# "/" (index.html landing page) bina login ke khulta hai.
EXEMPT_PATHS = ("/",)

EXEMPT_PREFIXES = (
    "/accounts/login/",
    "/accounts/signup/",
    "/accounts/leaving/",
    "/healthz/",
    "/admin/",
    "/static/",
    "/favicon.ico",
)

# API requests DRF (JWT/Session) khud authorize karta hai.
API_PREFIXES = (
    "/api/",
)

# Session key: browser/tab ne site chhodte waqt ye time save kiya.
LEAVE_KEY = "left_site_at"


class FarmerMiddleware:
    """
    1. Website pages ke liye login zaroori (index.html "/" ko chhodkar).
    2. Auto-logout: agar user ne tab/browser band kiya (pagehide beacon) aur
       SITE_LEAVE_GRACE_SECONDS ke andar koi nayi request nahi aayi, to logout.
       Reload / ek page se doosre page par jaane par nayi request turant aa jaati hai,
       isliye us case me logout nahi hota.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _expire_if_left(self, request):
        """True return karta hai agar session abhi logout kiya gaya."""
        if not request.user.is_authenticated:
            return False
        left_at = request.session.get(LEAVE_KEY)
        if left_at is None:
            return False
        grace = getattr(settings, "SITE_LEAVE_GRACE_SECONDS", 15)
        if request.path.startswith("/accounts/leaving/"):
            return False  # beacon khud marker set/clear karta hai
        if time.time() - float(left_at) > grace:
            logout(request)  # session flush
            return True
        # Reload / navigation: user wapas aa gaya -> marker hata do.
        del request.session[LEAVE_KEY]
        return False

    def __call__(self, request):
        request.farmer = None

        if self._expire_if_left(request) and not request.path.startswith(API_PREFIXES):
            if request.path in EXEMPT_PATHS or request.path.startswith(EXEMPT_PREFIXES):
                return self.get_response(request)
            # Auto-logout hone par index.html (home) par bhejo
            return redirect(reverse("farms:home"))

        # Let DRF/JWT handle API authentication and permissions.
        if request.path.startswith(API_PREFIXES):
            return self.get_response(request)

        user = request.user

        if user.is_authenticated:
            try:
                request.farmer = user.farmer_profile
            except ObjectDoesNotExist:
                request.farmer = FarmerProfile.objects.create(
                    user=user,
                    full_name=user.get_full_name() or user.username,
                )

        elif request.path not in EXEMPT_PATHS and not request.path.startswith(EXEMPT_PREFIXES):
            login_url = reverse(settings.LOGIN_URL)
            return redirect(f"{login_url}?next={request.get_full_path()}")

        return self.get_response(request)
