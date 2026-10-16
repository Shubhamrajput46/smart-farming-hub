"""
Notification banane ke 2 tareeke:
1. notify()        -> kisi event par turant (bikri hui, katayi darj hui...)
2. run_alerts()    -> time-based jaanch (katayi paas hai, sinchai due, paisa baaki, reminder...)
                      Yeh dashboard khulne par (30 min me ek baar) aur `manage.py generate_alerts` se chalta hai.
dedupe_key se ek hi alert baar-baar nahi banta.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError
from django.utils import timezone

from .models import Notification


def notify(farmer, title, message='', kind='system', severity='info', link='', key=None):
    if key:
        existing = Notification.objects.filter(farmer=farmer, dedupe_key=key).first()
        if existing:
            return None
        try:
            return Notification.objects.create(farmer=farmer, title=title, message=message, kind=kind,
                                               severity=severity, link=link, dedupe_key=key)
        except IntegrityError:
            return None
    return Notification.objects.create(farmer=farmer, title=title, message=message, kind=kind,
                                       severity=severity, link=link)


def _week(d):
    iso = d.isocalendar()
    return f"{iso[0]}w{iso[1]}"


def run_alerts(farmer):
    """Is kisan ke liye saare time-based alerts check karke naye notification banata hai. Count return karta hai."""
    from farms.models import Crop, CropOperationLog
    from finance.models import FarmExpense, FarmSale
    from accounts.models import FarmerDocument
    from .models import Reminder

    today = timezone.localdate()
    wk = _week(today)
    created = 0

    def push(*args, **kwargs):
        nonlocal created
        if notify(farmer, *args, **kwargs):
            created += 1

    for crop in Crop.objects.filter(land__farmer=farmer, is_active=True):
        link = f"/crops/{crop.pk}/"
        left = crop.days_to_harvest()
        if 0 <= left <= 7:
            push(f"Katayi nazdeek: {crop.name}", f"Katayi me {left} din bache hain. Thresher / majdoor book kar lein.",
                 kind='harvest', severity='warning', link=link, key=f"harvest-soon-{crop.pk}")
        elif left < 0:
            push(f"Katayi ka samay nikal gaya: {crop.name}", f"Anumaanit tarikh ko {-left} din ho gaye. Stage / utpadan update karein.",
                 kind='harvest', severity='danger', link=link, key=f"harvest-over-{crop.pk}-{wk}")

        if crop.stage in ('Vegetative', 'Flowering', 'GrainFilling') and crop.days_since_sowing() >= 7:
            last = (CropOperationLog.objects.filter(crop=crop, operation_type='Irrigation')
                    .order_by('-date').values_list('date', flat=True).first()) or crop.sowing_date
            gap = (today - last).days
            if gap >= 12:
                push(f"Sinchai due: {crop.name}", f"Pichli sinchai ko {gap} din ho gaye. Mitti ki nami check karein.",
                     kind='irrigation', severity='warning', link=f"/crop-care/add/?crop={crop.pk}&type=Irrigation",
                     key=f"irrigation-{crop.pk}-{wk}")

        days = crop.days_since_sowing()
        has_fert = CropOperationLog.objects.filter(crop=crop, operation_type='Fertilizer').exists()
        if 20 <= days <= 30 and not has_fert:
            push(f"Khad ka samay: {crop.name}", f"Buwai ko {days} din ho gaye, pehli khad / Urea abhi tak log nahi hui.",
                 kind='fertilizer', severity='info', link=f"/crop-care/add/?crop={crop.pk}&type=Fertilizer",
                 key=f"fert-first-{crop.pk}")

    for sale in FarmSale.objects.filter(farmer=farmer, payment_status__in=['Pending', 'Partial'],
                                        sale_date__lte=today - timedelta(days=7)):
        push(f"Paisa baaki: Rs {sale.balance}", f"{sale.buyer_name} se {sale.sale_date:%d %b} ki bikri ka paisa milna baaki hai.",
             kind='payment', severity='warning', link='/finance/sales/?status=Pending', key=f"recv-{sale.pk}-{wk}")

    for exp in FarmExpense.objects.filter(farmer=farmer, payment_status='Pending', date__lte=today - timedelta(days=15)):
        push(f"Udhaar chukana hai: Rs {exp.amount}", f"{exp.paid_to or 'Dukaan'} - {exp.title} ({exp.date:%d %b}).",
             kind='payment', severity='warning', link='/finance/expenses/?status=Pending', key=f"pay-{exp.pk}-{wk}")

    for rem in Reminder.objects.filter(farmer=farmer, is_done=False, due_date__lte=today + timedelta(days=1)):
        if rem.due_date < today:
            push(f"Chhoota hua kaam: {rem.title}", f"{rem.due_date:%d %b} ko karna tha.", kind='reminder',
                 severity='danger', link='/notifications/reminders/', key=f"rem-over-{rem.pk}-{wk}")
        elif rem.due_date == today:
            push(f"Aaj karna hai: {rem.title}", rem.notes, kind='reminder', severity='warning',
                 link='/notifications/reminders/', key=f"rem-today-{rem.pk}")
        else:
            push(f"Kal karna hai: {rem.title}", rem.notes, kind='reminder', severity='info',
                 link='/notifications/reminders/', key=f"rem-soon-{rem.pk}")

    for doc in FarmerDocument.objects.filter(farmer=farmer, expiry_date__isnull=False,
                                              expiry_date__lte=today + timedelta(days=30)):
        state = 'khatam ho chuka hai' if doc.expiry_date < today else f"{doc.expiry_date:%d %b %Y} ko khatam hoga"
        push(f"Document: {doc.title}", f"Yeh {state}. Renew karwa lein.", kind='document',
             severity='warning', link='/accounts/profile/', key=f"doc-{doc.pk}-{doc.expiry_date}")
    return created


def run_alerts_if_due(request, farmer, minutes=30):
    """Dashboard har baar na chalaye isliye session me last-run time rakhte hain."""
    now = timezone.now().timestamp()
    last = request.session.get('alerts_last_run', 0)
    if now - last >= minutes * 60:
        run_alerts(farmer)
        request.session['alerts_last_run'] = now
