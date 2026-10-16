from django.contrib.auth import get_user_model
from rest_framework import serializers
from accounts.models import FarmerProfile
from farms.models import Land, Crop, CropOperationLog, FarmAlert
from finance.models import FarmExpense, FarmSale
from ai_services.models import MandiPrice, Scheme

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if qs.exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        # Profile field requirements vary by project; do not guess required model fields.
        FarmerProfile.objects.get_or_create(user=user, defaults={"full_name": user.get_username()})
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = fields

class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = "__all__"
        read_only_fields = ("user",)

class LandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Land
        fields = "__all__"
        read_only_fields = ("farmer",)

def _owned_by_request_user(serializer, crop=None, land=None):
    """Doosre kisan ki land/crop se data jodne se rokta hai (API security)."""
    request = serializer.context.get("request")
    if request is None or not request.user.is_authenticated:
        return
    if land is not None and land.farmer.user_id != request.user.pk:
        raise serializers.ValidationError({"land": "Yeh land aapki nahi hai."})
    if crop is not None and crop.land.farmer.user_id != request.user.pk:
        raise serializers.ValidationError({"crop": "Yeh fasal aapki nahi hai."})


class CropOperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropOperationLog
        fields = "__all__"

    def validate(self, attrs):
        _owned_by_request_user(self, crop=attrs.get("crop"))
        return attrs

class CropSerializer(serializers.ModelSerializer):
    operations = CropOperationLogSerializer(many=True, read_only=True)
    total_cost = serializers.ReadOnlyField()
    total_revenue = serializers.ReadOnlyField()
    net_profit = serializers.ReadOnlyField()
    remaining_stock_quintals = serializers.ReadOnlyField()

    class Meta:
        model = Crop
        fields = "__all__"

    def validate(self, attrs):
        _owned_by_request_user(self, land=attrs.get("land"))
        return attrs

class FarmAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmAlert
        fields = "__all__"

class FarmExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmExpense
        fields = "__all__"
        read_only_fields = ("farmer",)

    def validate(self, attrs):
        _owned_by_request_user(self, crop=attrs.get("crop"))
        return attrs

class FarmSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmSale
        fields = "__all__"
        read_only_fields = ("farmer",)

    def validate(self, attrs):
        _owned_by_request_user(self, crop=attrs.get("crop"))
        return attrs

class MandiPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MandiPrice
        fields = "__all__"

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = "__all__"
