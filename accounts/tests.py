import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from farms.models import Land

User = get_user_model()


class HomeAndAutoLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('kisan', password='Pass@12345')
        self.other = User.objects.create_user('other', password='Pass@12345')

    # ---- index.html project start par khulta hai ----
    def test_root_shows_index_without_login(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'index.html')
        self.assertContains(r, reverse('accounts:login'))
        self.assertNotContains(r, '127.0.0.1:8000')

    def test_root_shows_dashboard_link_when_logged_in(self):
        self.client.login(username='kisan', password='Pass@12345')
        r = self.client.get('/')
        self.assertTemplateUsed(r, 'index.html')
        self.assertContains(r, reverse('farms:dashboard'))

    def test_dashboard_still_needs_login(self):
        r = self.client.get(reverse('farms:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('accounts:login'), r['Location'])

    # ---- auto logout ----
    def _login(self):
        self.client.login(username='kisan', password='Pass@12345')

    def test_leaving_then_returning_quickly_keeps_session(self):  # reload / navigation
        self._login()
        self.client.post(reverse('accounts:leaving'), {'action': 'leave'})
        r = self.client.get(reverse('farms:dashboard'))
        self.assertEqual(r.status_code, 200)

    @override_settings(SITE_LEAVE_GRACE_SECONDS=15)
    def test_leaving_and_not_returning_logs_out(self):
        self._login()
        self.client.post(reverse('accounts:leaving'), {'action': 'leave'})
        s = self.client.session
        s['left_site_at'] = time.time() - 60
        s.save()
        r = self.client.get(reverse('farms:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], reverse('farms:home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_manual_logout_goes_to_index(self):
        self._login()
        r = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(r, reverse('farms:home'), fetch_redirect_response=False)

    def test_healthz_is_public(self):
        r = self.client.get('/healthz/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})

    def test_custom_404_page(self):
        self._login()
        r = self.client.get('/yeh-page-nahi-hai/')
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'Yeh page nahi mila', status_code=404)

    def test_healthz_is_public(self):
        r = self.client.get('/healthz/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})

    def test_custom_404_page(self):
        self._login()
        r = self.client.get('/yeh-page-nahi-hai/')
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'Yeh page nahi mila', status_code=404)

    def test_media_requires_login_and_serves_file(self):
        import os, tempfile
        from django.conf import settings as dj
        d = tempfile.mkdtemp()
        open(os.path.join(d, 'a.txt'), 'w').write('hello')
        with override_settings(MEDIA_ROOT=d):
            from django.urls import clear_url_caches
            from importlib import reload
            import farming.urls as fu
            clear_url_caches(); reload(fu)
            r = self.client.get('/media/a.txt')
            self.assertEqual(r.status_code, 302)           # anonymous -> login
            self._login()
            r = self.client.get('/media/a.txt')
            self.assertEqual(r.status_code, 200)
            self.assertEqual(b''.join(r.streaming_content), b'hello')
        clear_url_caches(); reload(fu)

    def test_stay_clears_marker(self):
        self._login()
        self.client.post(reverse('accounts:leaving'), {'action': 'leave'})
        self.client.post(reverse('accounts:leaving'), {'action': 'stay'})
        s = self.client.session
        self.assertNotIn('left_site_at', s)

    def test_leaving_endpoint_post_only(self):
        self._login()
        self.assertEqual(self.client.get(reverse('accounts:leaving')).status_code, 405)

    def test_base_template_loads_api_and_csrf(self):
        self._login()
        html = self.client.get(reverse('farms:dashboard')).content.decode()
        self.assertIn('js/api.js', html)
        self.assertIn('name="csrf-token"', html)
        self.assertIn(reverse('accounts:leaving'), html)


class ApiOwnershipTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', password='Pass@12345')
        self.b = User.objects.create_user('b', password='Pass@12345')
        from accounts.models import FarmerProfile
        self.pa = FarmerProfile.objects.create(user=self.a, full_name='A')
        self.pb = FarmerProfile.objects.create(user=self.b, full_name='B')
        self.land_b = Land.objects.create(farmer=self.pb, title='B khet', total_area_acres=5)

    def test_cannot_create_crop_on_other_farmers_land(self):
        self.client.login(username='a', password='Pass@12345')
        r = self.client.post('/api/crops/', {
            'land': self.land_b.pk, 'name': 'Wheat', 'allocated_acres': 1,
            'expected_harvest_date': '2027-04-01',
        }, content_type='application/json')
        self.assertEqual(r.status_code, 400, r.content)

    def test_ai_assistant_requires_login(self):
        r = self.client.post('/api/ai/assistant/', {'prompt': 'hi'}, content_type='application/json')
        self.assertIn(r.status_code, (401, 403))
