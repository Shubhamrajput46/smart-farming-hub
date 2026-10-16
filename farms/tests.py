from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import FarmerProfile
from farms.models import Crop, CropOperationLog, Land
from finance.models import FarmExpense, FarmSale
from notifications.models import Notification, Reminder
from notifications.services import run_alerts


def make_farmer(username='ram'):
    user = User.objects.create_user(username, password='pass12345')
    return user, FarmerProfile.objects.create(user=user, full_name=username.title())


class FullFlowTests(TestCase):
    def setUp(self):
        self.user, self.farmer = make_farmer()
        self.client.login(username='ram', password='pass12345')
        self.today = timezone.localdate()
        self.land = Land.objects.create(farmer=self.farmer, title='Khet 1', total_area_acres=Decimal('5'))

    def crop(self, acres='3', **kw):
        data = dict(land=self.land, name='Gehun', allocated_acres=Decimal(acres),
                    sowing_date=self.today - timedelta(days=30), expected_harvest_date=self.today + timedelta(days=90))
        data.update(kw)
        return Crop.objects.create(**data)

    def test_login_required(self):
        self.client.logout()
        r = self.client.get(reverse('farms:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r['Location'])

    def test_signup_creates_profile(self):
        self.client.logout()
        r = self.client.post(reverse('accounts:signup'), {
            'full_name': 'Sita Devi', 'phone': '9999999999', 'village': 'X', 'district': 'Indore', 'state': 'MP',
            'username': 'sita', 'password1': 'Strong#Pass1', 'password2': 'Strong#Pass1'})
        self.assertEqual(r.status_code, 302, getattr(r, 'context', None) and r.context['form'].errors)
        self.assertTrue(FarmerProfile.objects.filter(user__username='sita', farmer_id_code__startswith='FRM-').exists())

    def test_land_crud(self):
        r = self.client.post(reverse('farms:land_add'), {
            'title': 'Naya', 'khasra_number': '1', 'total_area_acres': '2.5', 'soil_type': 'Red',
            'water_source': 'Well', 'irrigation_type': 'Drip', 'ownership': 'Own', 'notes': ''})
        self.assertEqual(r.status_code, 302)
        land = Land.objects.get(title='Naya')
        self.client.post(reverse('farms:land_edit', args=[land.pk]), {
            'title': 'Naya2', 'khasra_number': '1', 'total_area_acres': '3', 'soil_type': 'Red',
            'water_source': 'Well', 'irrigation_type': 'Drip', 'ownership': 'Own', 'notes': ''})
        land.refresh_from_db()
        self.assertEqual(land.title, 'Naya2')
        self.client.post(reverse('farms:land_delete', args=[land.pk]))
        self.assertFalse(Land.objects.filter(pk=land.pk).exists())

    def crop_post(self, **over):
        d = {'land': self.land.pk, 'name': 'Soybean', 'season': 'Kharif', 'season_year': '2026',
             'allocated_acres': '2', 'seed_info': '', 'sowing_date': str(self.today),
             'expected_harvest_date': str(self.today + timedelta(days=100)), 'stage': 'Sowing',
             'expected_yield_quintal': '20', 'notes': ''}
        d.update(over)
        return self.client.post(reverse('farms:crop_add'), d)

    def test_crop_area_validation(self):
        self.crop('4')
        r = self.crop_post(allocated_acres='2')  # sirf 1 acre bacha
        self.assertEqual(r.status_code, 200)
        self.assertIn('allocated_acres', r.context['form'].errors)
        r = self.crop_post(allocated_acres='1')
        self.assertEqual(r.status_code, 302)

    def test_crop_date_validation(self):
        r = self.crop_post(expected_harvest_date=str(self.today - timedelta(days=1)))
        self.assertIn('expected_harvest_date', r.context['form'].errors)

    def test_operation_syncs_expense(self):
        crop = self.crop()
        r = self.client.post(reverse('farms:operation_add'), {
            'crop': crop.pk, 'operation_type': 'Labour' if False else 'Weeding', 'date': str(self.today),
            'labour_count': '5', 'labour_cost_per_person': '300', 'material_used': '', 'hours_run': '0',
            'total_cost': '', 'notes': ''})
        self.assertEqual(r.status_code, 302)
        op = CropOperationLog.objects.get()
        self.assertEqual(op.total_cost, Decimal('1500'))
        exp = FarmExpense.objects.get(source_operation=op)
        self.assertEqual(exp.amount, Decimal('1500'))
        self.assertEqual(exp.category, 'Labour')
        self.assertEqual(crop.total_expense(), Decimal('1500'))  # double count nahi
        # edit
        self.client.post(reverse('farms:operation_edit', args=[op.pk]), {
            'crop': crop.pk, 'operation_type': 'Weeding', 'date': str(self.today), 'labour_count': '5',
            'labour_cost_per_person': '300', 'material_used': '', 'hours_run': '0', 'total_cost': '2000', 'notes': ''})
        self.assertEqual(FarmExpense.objects.get(source_operation=op).amount, Decimal('2000'))
        # expense edit op par redirect
        r = self.client.get(reverse('finance:expense_edit', args=[exp.pk]))
        self.assertEqual(r.status_code, 302)
        # delete
        self.client.post(reverse('farms:operation_delete', args=[op.pk]))
        self.assertEqual(FarmExpense.objects.count(), 0)

    def test_harvest_and_sales_flow(self):
        crop = self.crop('2')
        # utpadan se pehle bikri nahi
        r = self.client.get(reverse('finance:sale_add'))
        self.assertEqual(r.status_code, 302)
        r = self.client.post(reverse('farms:crop_harvest', args=[crop.pk]), {
            'actual_yield_quintal': '20', 'actual_harvest_date': str(self.today), 'mark_completed': 'on'})
        self.assertEqual(r.status_code, 302)
        crop.refresh_from_db()
        self.assertEqual(crop.stage, 'Completed')
        self.assertFalse(crop.is_active)
        self.assertEqual(self.land.available_area(), Decimal('5'))  # zameen khaali
        base = {'crop': crop.pk, 'buyer_name': 'Gupta', 'sale_place': 'Mandi', 'price_per_quintal': '5000',
                'deductions': '500', 'amount_received': '0', 'sale_date': str(self.today), 'remarks': ''}
        r = self.client.post(reverse('finance:sale_add'), dict(base, quantity_quintals='25'))
        self.assertIn('quantity_quintals', r.context['form'].errors)  # stock se zyada
        r = self.client.post(reverse('finance:sale_add'), dict(base, quantity_quintals='10', amount_received='20000'))
        self.assertEqual(r.status_code, 302)
        sale = FarmSale.objects.get()
        self.assertEqual(sale.total_amount, Decimal('49500'))
        self.assertEqual(sale.payment_status, 'Partial')
        self.assertEqual(crop.remaining_stock(), Decimal('10'))
        # paisa mila
        self.client.post(reverse('finance:sale_receive', args=[sale.pk]), {'amount': '29500'})
        sale.refresh_from_db()
        self.assertEqual(sale.payment_status, 'Paid')
        self.assertEqual(Notification.objects.filter(kind='sale').count(), 1)
        # zyada receive nahi
        self.client.post(reverse('finance:sale_receive', args=[sale.pk]), {'amount': '10'})
        sale.refresh_from_db()
        self.assertEqual(sale.amount_received, Decimal('49500'))
        # edit me apna hi stock dobara count na ho: 20 Qt valid (10 baki + 10 apna), 21 Qt invalid
        r = self.client.post(reverse('finance:sale_edit', args=[sale.pk]), dict(base, quantity_quintals='21', amount_received='49500'))
        self.assertIn('quantity_quintals', r.context['form'].errors)
        r = self.client.post(reverse('finance:sale_edit', args=[sale.pk]), dict(base, quantity_quintals='20', amount_received='49500'))
        self.assertEqual(r.status_code, 302)
        sale.refresh_from_db()
        self.assertEqual(sale.payment_status, 'Partial')
        # delete
        self.client.post(reverse('finance:sale_delete', args=[sale.pk]))
        self.assertEqual(crop.remaining_stock(), Decimal('20'))

    def test_expense_crud_and_udhaar(self):
        r = self.client.post(reverse('finance:expense_add'), {
            'title': 'DAP', 'category': 'Fertilizer', 'amount': '6500', 'date': str(self.today), 'crop': '',
            'paid_to': 'Sharma', 'payment_method': 'Udhaar', 'payment_status': 'Paid', 'description': ''})
        self.assertEqual(r.status_code, 302)
        e = FarmExpense.objects.get()
        self.assertEqual(e.payment_status, 'Pending')  # udhaar => pending
        self.assertTrue(Notification.objects.filter(kind='payment').exists())
        self.client.post(reverse('finance:expense_paid', args=[e.pk]))
        e.refresh_from_db()
        self.assertEqual(e.payment_status, 'Paid')
        self.assertEqual(self.client.get(reverse('finance:expenses') + '?q=DAP&category=Fertilizer').status_code, 200)
        self.client.post(reverse('finance:expense_delete', args=[e.pk]))
        self.assertEqual(FarmExpense.objects.count(), 0)

    def test_alerts_and_notifications(self):
        crop = self.crop(expected_harvest_date=self.today + timedelta(days=3))
        Reminder.objects.create(farmer=self.farmer, title='Thresher', due_date=self.today)
        n = run_alerts(self.farmer)
        self.assertGreaterEqual(n, 2)
        self.assertEqual(run_alerts(self.farmer), 0)  # dobara duplicate nahi
        self.assertTrue(Notification.objects.filter(kind='harvest').exists())
        self.assertEqual(self.client.get(reverse('notifications:list')).status_code, 200)
        data = self.client.get(reverse('notifications:api_summary')).json()
        self.assertGreater(data['unread'], 0)
        nid = Notification.objects.first().pk
        self.client.post(reverse('notifications:read', args=[nid]))
        self.assertTrue(Notification.objects.get(pk=nid).is_read)
        self.client.post(reverse('notifications:read_all'))
        self.assertEqual(Notification.objects.filter(is_read=False).count(), 0)
        self.client.post(reverse('notifications:clear_read'))
        self.assertEqual(Notification.objects.count(), 0)

    def test_reminder_crud(self):
        r = self.client.post(reverse('notifications:reminder_add'), {'title': 'Spray', 'due_date': str(self.today), 'crop': '', 'notes': ''})
        self.assertEqual(r.status_code, 302)
        rem = Reminder.objects.get()
        self.client.post(reverse('notifications:reminder_toggle', args=[rem.pk]))
        rem.refresh_from_db()
        self.assertTrue(rem.is_done)
        self.client.post(reverse('notifications:reminder_delete', args=[rem.pk]))
        self.assertEqual(Reminder.objects.count(), 0)

    def test_data_isolation(self):
        crop = self.crop()
        self.client.logout()
        make_farmer('shyam')
        self.client.login(username='shyam', password='pass12345')
        for name in ('crop_detail', 'crop_edit', 'crop_delete', 'crop_harvest'):
            self.assertEqual(self.client.get(reverse(f'farms:{name}', args=[crop.pk])).status_code, 404, name)
        self.assertEqual(self.client.get(reverse('farms:land_detail', args=[self.land.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('farms:crop_list')).context['page'].paginator.count, 0)

    def test_document_and_profile(self):
        self.assertEqual(self.client.get(reverse('accounts:profile')).status_code, 200)
        self.assertEqual(self.client.get(reverse('accounts:profile_edit')).status_code, 200)
        r = self.client.post(reverse('accounts:document_add'), {'title': 'Aadhaar', 'doc_type': 'Aadhaar', 'expiry_date': ''})
        self.assertEqual(r.status_code, 302)

    def test_all_pages_render_with_demo_data(self):
        self.client.logout()
        call_command('seed_demo', verbosity=0)
        self.assertTrue(self.client.login(username='demo', password='demo12345'))
        crop = Crop.objects.filter(land__farmer__user__username='demo').first()
        urls = [reverse('farms:dashboard'), reverse('farms:land_list'), reverse('farms:land_add'),
                reverse('farms:land_detail', args=[crop.land.pk]), reverse('farms:crop_list'), reverse('farms:crop_list') + '?status=all&q=Geh',
                reverse('farms:crop_add'), reverse('farms:crop_detail', args=[crop.pk]), reverse('farms:crop_edit', args=[crop.pk]),
                reverse('farms:crop_harvest', args=[crop.pk]), reverse('farms:crop_delete', args=[crop.pk]),
                reverse('farms:operation_list'), reverse('farms:operation_add') + f'?crop={crop.pk}&type=Irrigation',
                reverse('finance:expenses'), reverse('finance:expense_add'), reverse('finance:sales'), reverse('finance:sale_add'),
                reverse('finance:reports'), reverse('finance:reports') + '?from=2020-01-01&crop=' + str(crop.pk),
                reverse('finance:export', args=['expenses']), reverse('finance:export', args=['sales']),
                reverse('notifications:list'), reverse('notifications:list') + '?filter=unread', reverse('notifications:reminders'),
                reverse('notifications:reminders') + '?show=all', reverse('notifications:reminder_add'),
                reverse('accounts:profile'), reverse('ai_services:market'), reverse('ai_services:loan_subsidy'),
                reverse('ai_services:pest_detection')]
        for u in urls:
            r = self.client.get(u)
            self.assertEqual(r.status_code, 200, u)
        # mobile hamburger + bell markup present
        html = self.client.get(reverse('farms:dashboard')).content.decode()
        self.assertIn('id="menuToggle"', html)
        self.assertIn('id="notifBell"', html)
