"""Chhote helper functions jo saare apps use karte hain."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .models import ActivityLog


def log_activity(farmer, title):
    ActivityLog.objects.create(farmer=farmer, title=title[:250])


def paginate(request, queryset, per_page=15):
    """(page_obj, querystring_without_page) return karta hai."""
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return page_obj, params.urlencode()


def confirm_delete(request, obj, success_url, label, warning='', cancel_url=None):
    """GET -> confirm page, POST -> delete. Har module ka DELETE yahi use karta hai."""
    if request.method == 'POST':
        obj.delete()
        messages.warning(request, f"{label} delete kar diya gaya.")
        return redirect(success_url)
    return render(request, 'generic_delete.html', {
        'object_label': label,
        'warning': warning,
        'cancel_url': cancel_url or success_url,
    })
