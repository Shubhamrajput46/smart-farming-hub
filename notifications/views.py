from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import confirm_delete, paginate

from .forms import ReminderForm
from .models import Notification, Reminder
from .services import run_alerts


def notification_list_view(request):
    qs = Notification.objects.filter(farmer=request.farmer)
    flt = request.GET.get('filter', 'all')
    if flt == 'unread':
        qs = qs.filter(is_read=False)
    elif flt in dict(Notification.KINDS):
        qs = qs.filter(kind=flt)
    page, querystring = paginate(request, qs, 20)
    return render(request, 'notification_list.html', {
        'page': page, 'qs': querystring, 'flt': flt, 'kinds': Notification.KINDS})


def _back(request, default='notifications:list'):
    nxt = request.POST.get('next', '')
    if nxt.startswith('/') and not nxt.startswith('//'):
        return redirect(nxt)
    return redirect(default)


@require_POST
def mark_read_view(request, pk):
    n = get_object_or_404(Notification, pk=pk, farmer=request.farmer)
    n.is_read = True
    n.save(update_fields=['is_read'])
    return redirect(n.link) if n.link and request.POST.get('open') else _back(request)


@require_POST
def mark_all_read_view(request):
    Notification.objects.filter(farmer=request.farmer, is_read=False).update(is_read=True)
    messages.success(request, 'Saari soochnayein padhi hui mark ho gayin.')
    return _back(request)


@require_POST
def delete_view(request, pk):
    get_object_or_404(Notification, pk=pk, farmer=request.farmer).delete()
    return _back(request)


@require_POST
def clear_read_view(request):
    Notification.objects.filter(farmer=request.farmer, is_read=True).delete()
    messages.warning(request, 'Padhi hui soochnayein hata di gayin.')
    return _back(request)


@require_POST
def refresh_view(request):
    n = run_alerts(request.farmer)
    messages.success(request, f"{n} nayi soochna mili." if n else 'Abhi koi nayi soochna nahi hai.')
    return _back(request)


def api_summary_view(request):
    """JS har minute is se badge update karta hai."""
    qs = Notification.objects.filter(farmer=request.farmer)
    latest = qs.filter(is_read=False).first()
    return JsonResponse({
        'unread': qs.filter(is_read=False).count(),
        'latest': {'id': latest.pk, 'title': latest.title, 'severity': latest.severity} if latest else None,
    })


# ---------------------------------------------------------------- Reminders
def reminder_list_view(request):
    show = request.GET.get('show', 'pending')
    qs = Reminder.objects.filter(farmer=request.farmer).select_related('crop')
    if show == 'pending':
        qs = qs.filter(is_done=False)
    elif show == 'done':
        qs = qs.filter(is_done=True)
    return render(request, 'reminder_list.html', {'reminders': qs, 'show': show, 'today': timezone.localdate()})


def reminder_add_view(request):
    initial = {'crop': request.GET.get('crop')} if request.GET.get('crop') else {}
    form = ReminderForm(request.POST or None, farmer=request.farmer, initial=initial)
    if request.method == 'POST' and form.is_valid():
        r = form.save(commit=False)
        r.farmer = request.farmer
        r.save()
        run_alerts(request.farmer)
        messages.success(request, 'Yaad-dihani save ho gayi. Samay aane par soochna milegi.')
        return redirect('notifications:reminders')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Nayi Yaad-dihani', 'back_url': 'notifications:reminders'})


def reminder_edit_view(request, pk):
    r = get_object_or_404(Reminder, pk=pk, farmer=request.farmer)
    form = ReminderForm(request.POST or None, instance=r, farmer=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Yaad-dihani update ho gayi.')
        return redirect('notifications:reminders')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Yaad-dihani Edit', 'back_url': 'notifications:reminders'})


def reminder_delete_view(request, pk):
    r = get_object_or_404(Reminder, pk=pk, farmer=request.farmer)
    return confirm_delete(request, r, 'notifications:reminders', f"Yaad-dihani '{r.title}'")


@require_POST
def reminder_toggle_view(request, pk):
    r = get_object_or_404(Reminder, pk=pk, farmer=request.farmer)
    r.is_done = not r.is_done
    r.save()
    messages.success(request, 'Kaam poora mark ho gaya.' if r.is_done else 'Kaam wapas pending kiya.')
    return _back(request, 'notifications:reminders')
