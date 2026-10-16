from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import FarmerProfile
from farms.models import Crop, CropOperationLog, Land
from finance.models import FarmExpense, FarmSale
from notifications.models import Reminder
from notifications.services import run_alerts


class Command(BaseCommand):
    help = "Demo kisan (username: demo / password: demo12345) aur sample data banata hai."

    def handle(self, *args, **options):
        if User.objects.filter(username='demo').exists():
            self.stdout.write('Demo user pehle se hai.')
            return
        today = timezone.localdate()
        user = User.objects.create_user('demo', password='demo12345')
        farmer = FarmerProfile.objects.create(user=user, full_name='Ramesh Patidar', phone='9876543210',
                                              village='Depalpur', district='Indore', experience_years=12, is_verified=True)
        l1 = Land.objects.create(farmer=farmer, title='Nadi wala khet', khasra_number='142/2', total_area_acres=Decimal('5'),
                                 soil_type='Black Cotton', water_source='Borewell', irrigation_type='Drip')
        Land.objects.create(farmer=farmer, title='Sadak kinare', khasra_number='88', total_area_acres=Decimal('3'),
                            ownership='Leased', irrigation_type='Flood')

        wheat = Crop.objects.create(land=l1, name='Gehun Sharbati', season='Rabi', allocated_acres=Decimal('3'),
                                    sowing_date=today - timedelta(days=95), expected_harvest_date=today + timedelta(days=5),
                                    stage='GrainFilling', expected_yield_quintal=Decimal('60'), seed_info='Sharbati 1544, 120 kg')
        soy = Crop.objects.create(land=l1, name='Soybean 9560', season='Kharif', allocated_acres=Decimal('2'),
                                  sowing_date=today - timedelta(days=150), expected_harvest_date=today - timedelta(days=30),
                                  actual_harvest_date=today - timedelta(days=28), stage='Completed',
                                  expected_yield_quintal=Decimal('20'), actual_yield_quintal=Decimal('22'))

        def op(crop, t, days_ago, labour=0, rate=0, material='', hours=0, cost=0):
            CropOperationLog.objects.create(crop=crop, operation_type=t, date=today - timedelta(days=days_ago),
                                            labour_count=labour, labour_cost_per_person=rate, material_used=material,
                                            hours_run=hours, total_cost=cost)
        op(wheat, 'Plowing', 100, hours=4, cost=3200, material='Rotavator')
        op(wheat, 'Sowing', 95, labour=4, rate=400)
        op(wheat, 'Irrigation', 75, hours=6, cost=900)
        op(wheat, 'Fertilizer', 70, material='2 bori Urea', cost=1200)
        op(wheat, 'Weeding', 50, labour=6, rate=350)
        op(soy, 'Sowing', 150, labour=3, rate=400)
        op(soy, 'Spray', 110, material='Keetnashak 500ml', cost=850)
        FarmExpense.objects.create(farmer=farmer, crop=wheat, title='Gehun beej 120 kg', category='Seed', amount=4800,
                                   date=today - timedelta(days=97), paid_to='Krishi Kendra')
        FarmExpense.objects.create(farmer=farmer, title='DAP 5 bori', category='Fertilizer', amount=6500,
                                   date=today - timedelta(days=20), paid_to='Sharma Khad Bhandar',
                                   payment_method='Udhaar', payment_status='Pending')
        FarmSale.objects.create(farmer=farmer, crop=soy, buyer_name='Indore Mandi - Gupta Traders', quantity_quintals=Decimal('15'),
                                price_per_quintal=Decimal('4900'), deductions=Decimal('900'), amount_received=Decimal('50000'),
                                sale_date=today - timedelta(days=20))
        Reminder.objects.create(farmer=farmer, crop=wheat, title='Thresher book karna', due_date=today + timedelta(days=1))
        Reminder.objects.create(farmer=farmer, title='Bijli bill bharna', due_date=today - timedelta(days=1))
        run_alerts(farmer)
        try:
            from ai_services.services import fetch_live_mandi_rates
            fetch_live_mandi_rates()
        except Exception:
            pass
        self.stdout.write(self.style.SUCCESS('Demo ready -> username: demo | password: demo12345'))
