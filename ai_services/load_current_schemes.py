from django.core.management.base import BaseCommand
from ai_services.models import Scheme

class Command(BaseCommand):
    help = "Loads current government schemes and subsidies with AI criteria"

    def handle(self, *args, **kwargs):
        SCHEMES_DATA = [
            {
                "title": "PM KUSUM Solar Agriculture Pump Scheme",
                "category": "Solar",
                "state": "Madhya Pradesh",
                "description": "Khet par 3HP se 7.5HP solar pump lagane par 60% tak direct subsidy milti hai taaki diesel aur electricity bill zero ho sake.",
                "min_land_acres": 0.5,
                "max_land_acres": 50.0,
                "target_crops": "All",
                "subsidy_percentage": 60,
                "max_benefit_amount": 180000.00,
                "official_link": "https://pmkusum.mnre.gov.in"
            },
            {
                "title": "Micro Irrigation Subsidy (Per Drop More Crop - Drip/Sprinkler)",
                "category": "Subsidy",
                "state": "Madhya Pradesh",
                "description": "Drip aur Sprinkler lagane par small/marginal farmers ko 55% aur large farmers ko 45% capital subsidy milti hai.",
                "min_land_acres": 1.0,
                "max_land_acres": 12.5,
                "target_crops": "Wheat, Soybean, Maize, Cotton, Vegetables",
                "subsidy_percentage": 55,
                "max_benefit_amount": 65000.00,
                "official_link": "https://pmksy.gov.in"
            },
            {
                "title": "PM-Kisan Samman Nidhi & MP Kisan Kalyan Combined",
                "category": "Subsidy",
                "state": "Madhya Pradesh",
                "description": "Kisaan ko saalana kul ₹12,000 (Central ₹6,000 + MP State ₹6,000) direct bank transfer me 3 barabar kisto me milte hain.",
                "min_land_acres": 0.1,
                "max_land_acres": 100.0,
                "target_crops": "All",
                "subsidy_percentage": 100,
                "max_benefit_amount": 12000.00,
                "official_link": "https://saara.mp.gov.in"
            },
            {
                "title": "E-Krishi Yantra Anudan (Rotavator & Harvester Subsidy)",
                "category": "Machinery",
                "state": "Madhya Pradesh",
                "description": "Tractor, Rotavator, Seed Drill aur Combine Harvester khareedne par MP DBT portal par 40% se 50% subsidy lottery basis par milti hai.",
                "min_land_acres": 2.0,
                "max_land_acres": 100.0,
                "target_crops": "Wheat, Soybean, Gram",
                "subsidy_percentage": 50,
                "max_benefit_amount": 150000.00,
                "official_link": "https://dbt.mpdage.org"
            },
            {
                "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "category": "Insurance",
                "state": "All India",
                "description": "Rabi fasal par 1.5% aur Kharif par 2% premium dekar baadh, sookha, ya keede se fasal nuksaan par 100% bima claim lein.",
                "min_land_acres": 0.1,
                "max_land_acres": 100.0,
                "target_crops": "Wheat, Soybean, Paddy, Mustard",
                "subsidy_percentage": 85,
                "max_benefit_amount": 75000.00,
                "official_link": "https://pmfby.gov.in"
            },
            {
                "title": "Kisan Credit Card (KCC) Low-Interest Crop Loan",
                "category": "Loan",
                "state": "All India",
                "description": "Time par repayment karne par 3% interest subvention ke sath effective byaaj dar sirf 4% saalana lagti hai.",
                "min_land_acres": 0.5,
                "max_land_acres": 100.0,
                "target_crops": "All",
                "subsidy_percentage": 3,
                "max_benefit_amount": 300000.00,
                "official_link": "https://www.myscheme.gov.in/schemes/kcc"
            }
        ]

        for s in SCHEMES_DATA:
            Scheme.objects.update_or_create(
                title=s["title"],
                defaults=s
            )
        self.stdout.write(self.style.SUCCESS("All AI-enabled schemes loaded successfully!"))