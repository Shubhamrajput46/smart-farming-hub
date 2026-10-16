from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.models import FarmerProfile
from farms.models import Land, Crop, CropOperationLog
from finance.models import FarmExpense, FarmSale
from ai_services.models import MandiPrice, Scheme
from .serializers import (
    UserRegisterSerializer, FarmerProfileSerializer, LandSerializer, CropSerializer,
    CropOperationLogSerializer, FarmExpenseSerializer, FarmSaleSerializer,
    MandiPriceSerializer, SchemeSerializer,
)
from .paginator import StandardResultsSetPagination
from .throttles import OpenAIUserRateThrottle, OpenAIAnonRateThrottle
from .openai_service import ask_openai

User = get_user_model()

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = FarmerProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        profile, _ = FarmerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.get_username()},
        )
        return profile

class FarmerScopedViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def farmer_profile(self):
        profile, _ = FarmerProfile.objects.get_or_create(
            user=self.request.user,
            defaults={"full_name": self.request.user.get_username()},
        )
        return profile

class LandViewSet(FarmerScopedViewSet):
    serializer_class = LandSerializer
    def get_queryset(self):
        return Land.objects.filter(farmer=self.farmer_profile())
    def perform_create(self, serializer):
        serializer.save(farmer=self.farmer_profile())

class CropViewSet(FarmerScopedViewSet):
    serializer_class = CropSerializer
    def get_queryset(self):
        return Crop.objects.filter(land__farmer=self.farmer_profile())

class CropOperationLogViewSet(FarmerScopedViewSet):
    serializer_class = CropOperationLogSerializer
    def get_queryset(self):
        # Restrict logs to crops on lands owned by the current profile.
        return CropOperationLog.objects.filter(crop__land__farmer=self.farmer_profile())

    def perform_create(self, serializer):
        crop = serializer.validated_data.get("crop")
        if not crop or crop.land.farmer_id != self.farmer_profile().pk:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add operation logs to your own crops.")
        serializer.save()

class ExpenseViewSet(FarmerScopedViewSet):
    serializer_class = FarmExpenseSerializer
    def get_queryset(self):
        return FarmExpense.objects.filter(farmer=self.farmer_profile())
    def perform_create(self, serializer):
        serializer.save(farmer=self.farmer_profile())

class SaleViewSet(FarmerScopedViewSet):
    serializer_class = FarmSaleSerializer
    def get_queryset(self):
        return FarmSale.objects.filter(farmer=self.farmer_profile())
    def perform_create(self, serializer):
        serializer.save(farmer=self.farmer_profile())


class MandiPriceListAPIView(generics.ListAPIView):
    queryset = MandiPrice.objects.all()
    serializer_class = MandiPriceSerializer
    permission_classes = (AllowAny,)
    pagination_class = StandardResultsSetPagination

    filterset_fields = ("crop_name", "market_name")
    search_fields = ("crop_name", "market_name")
    ordering_fields = ("crop_name", "market_name", "today_price", "updated_at")
    ordering = ("-updated_at",)

class SchemeListAPIView(generics.ListAPIView):
    queryset = Scheme.objects.filter(is_active=True)
    serializer_class = SchemeSerializer
    permission_classes = (AllowAny,)
    pagination_class = StandardResultsSetPagination

class OpenAIAssistantAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (OpenAIUserRateThrottle, OpenAIAnonRateThrottle)

    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not isinstance(prompt, str) or not prompt.strip():
            return Response({"detail": "prompt is required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(prompt) > 4000:
            return Response({"detail": "prompt must be 4000 characters or fewer."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            answer = ask_openai(prompt.strip())
        except RuntimeError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"answer": answer})
