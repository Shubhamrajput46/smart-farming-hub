from django.core.management.base import BaseCommand

from accounts.models import FarmerProfile
from notifications.services import run_alerts


class Command(BaseCommand):
    help = "Saare kisano ke liye time-based alerts banata hai (cron / Task Scheduler me roz chalayein)."

    def handle(self, *args, **options):
        total = sum(run_alerts(f) for f in FarmerProfile.objects.all())
        self.stdout.write(self.style.SUCCESS(f"{total} nayi notifications bani."))
