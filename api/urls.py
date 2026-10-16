from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterAPIView, ProfileAPIView, CustomTokenObtainPairView, CustomTokenRefreshView,
    LandViewSet, CropViewSet, CropOperationLogViewSet, ExpenseViewSet, SaleViewSet,
    MandiPriceListAPIView, SchemeListAPIView, OpenAIAssistantAPIView,
)

router = DefaultRouter()
router.register("lands", LandViewSet, basename="api-land")
router.register("crops", CropViewSet, basename="api-crop")
router.register("operations", CropOperationLogViewSet, basename="api-operation")
router.register("expenses", ExpenseViewSet, basename="api-expense")
router.register("sales", SaleViewSet, basename="api-sale")

urlpatterns = [
    path("auth/signup/", RegisterAPIView.as_view(), name="api-register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/profile/", ProfileAPIView.as_view(), name="api-profile"),
    path("services/mandi-prices/", MandiPriceListAPIView.as_view(), name="api-mandi"),
    path("services/schemes/", SchemeListAPIView.as_view(), name="api-schemes"),
    path("ai/assistant/", OpenAIAssistantAPIView.as_view(), name="api-openai-assistant"),
    path("", include(router.urls)),
]
