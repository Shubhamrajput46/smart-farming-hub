
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "farming.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import FarmerProfile
from farms.models import Land

User = get_user_model()


def run_security_tests():
    print("\n=== FARMER DATA SECURITY TESTS ===")

    # Use existing users; do not modify or delete their records.
    username_a = input("Farmer A username: ").strip()
    username_b = input("Farmer B username: ").strip()

    user_a = User.objects.filter(username=username_a).first()
    user_b = User.objects.filter(username=username_b).first()

    if not user_a or not user_b:
        print("ERROR: Dono users database mein hone chahiye.")
        return

    if user_a.pk == user_b.pk:
        print("ERROR: Farmer A aur Farmer B alag users hone chahiye.")
        return

    profile_a = FarmerProfile.objects.filter(user=user_a).first()
    profile_b = FarmerProfile.objects.filter(user=user_b).first()

    if not profile_a or not profile_b:
        print("ERROR: Dono users ke FarmerProfile hone chahiye.")
        return

    land_b = Land.objects.filter(farmer=profile_b).first()

    if not land_b:
        print("SKIP: Farmer B ki land nahi hai; pehle test data banao.")
        return

    # Authenticate as Farmer A.
    client = APIClient()
    client.force_authenticate(user=user_a)

    # Attempt to read Farmer B's land.
    response = client.get(f"/api/lands/{land_b.pk}/")

    if response.status_code == 404:
        print("PASS: Farmer A cannot read Farmer B's land.")
    else:
        print(
            "FAIL: Cross-farmer land read returned",
            response.status_code,
        )
        if response.status_code == 200:
            print("CRITICAL: Farmer B's land data was exposed!")

    print("\nSecurity test completed.")


if __name__ == "__main__":
    run_security_tests()
