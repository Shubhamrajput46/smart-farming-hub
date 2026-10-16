# AgroSmart API — corrected integration package

This package is an **API app**, not the complete Django project. It assumes your existing project has:
`accounts.FarmerProfile`, `farms.Land`, `farms.Crop`, `farms.CropOperationLog`,
`finance.FarmExpense`, `finance.FarmSale`, and `ai_services.MandiPrice` / `Scheme`.
Model field names vary between projects; see compatibility notes below.

## 1. Install packages

```bash
pip install djangorestframework djangorestframework-simplejwt drf-spectacular django-filter openai
```

OpenAI is called using the HTTPS Responses API with Python's standard library; `openai` is optional.

## 2. Add to `settings.py`

```python
import os

INSTALLED_APPS += [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "api",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "api.paginator.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": [
        "api.throttles.ApiAnonRateThrottle",
        "api.throttles.ApiUserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/minute",
        "user": "120/minute",
        "openai_anon": "2/minute",
        "openai_user": "5/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AgroSmart API",
    "DESCRIPTION": "JWT-secured farmer APIs and agricultural services",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TIMEOUT = 30
```

Do not commit `.env` or hard-code the OpenAI key in Python/JavaScript. For local development, put `OPENAI_API_KEY=...` in your environment or load it using your existing dotenv setup.

## 3. Add to the project's root `urls.py`

Merge these paths into your existing URL patterns (do not replace existing app routes):

```python
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns += [
    path("api/v1/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

Docs: `/api/docs/`, ReDoc: `/api/redoc/`, schema: `/api/schema/`.

## 4. Test endpoints

- `POST /api/v1/auth/register/` body: `{"username":"farmer1","email":"farmer@example.com","password":"StrongPass123"}`
- `POST /api/v1/auth/token/` body: `{"username":"farmer1","password":"StrongPass123"}`
- Send `Authorization: Bearer <access>` for protected endpoints.
- `POST /api/v1/ai/assistant/` body: `{"prompt":"How can I reduce weeds in wheat?"}` (JWT required).
- `GET /api/v1/services/mandi-prices/`
- `GET /api/v1/services/schemes/`
- Pagination: `?page=1&page_size=20`

## Important compatibility notes

1. This zip cannot safely change your full project's models or migrations because only the `api/` directory was supplied.
2. `FarmerProfile` must have a `user` one-to-one/foreign key. The registration/profile defaults assume `full_name` exists; remove that default if your model uses another field name.
3. `CropOperationLog` is assumed to have a `crop` FK and `Crop.land` plus `Land.farmer`. Adjust the relationship path if your models differ.
4. The mandi filters assume `crop_name`, `state`, `district`, `market` fields. Remove or update `filterset_fields` to match your actual `MandiPrice` model.
5. The code scopes land/crop/log/finance APIs to the logged-in farmer. Verify `FarmExpense.farmer` and `FarmSale.farmer` point to `FarmerProfile`.
6. The package does not add database models, so no new migrations are expected from this app.
7. Django REST Framework throttling is application-level fairness, not a full DDoS defence. Use HTTPS, production rate limiting, secure secrets, and monitoring when deploying.
