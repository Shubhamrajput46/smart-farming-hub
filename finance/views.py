import csv
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.utils import confirm_delete, log_activity, paginate
from farms.models import Crop
from notifications.services import notify

from .forms import ExpenseForm, SaleForm
from .models import FarmExpense, FarmSale


def _d(v):
    return v or Decimal('0')


def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


# ------------------------------------------------------------------ EXPENSES
def expense_list_view(request):
    qs = FarmExpense.objects.filter(farmer=request.farmer).select_related('crop')
    cat, status, crop_id = request.GET.get('category', ''), request.GET.get('status', ''), request.GET.get('crop', '')
    q = request.GET.get('q', '').strip()
    if cat:
        qs = qs.filter(category=cat)
    if status:
        qs = qs.filter(payment_status=status)
    if crop_id.isdigit():
        qs = qs.filter(crop_id=crop_id)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(paid_to__icontains=q))
    total = _d(qs.aggregate(t=Sum('amount'))['t'])
    pending = _d(qs.filter(payment_status='Pending').aggregate(t=Sum('amount'))['t'])
    page, querystring = paginate(request, qs, 15)
    return render(request, 'expense_list.html', {
        'page': page, 'qs': querystring, 'total': total, 'pending': pending,
        'categories': FarmExpense.CATEGORIES, 'crops': Crop.objects.filter(land__farmer=request.farmer),
        'sel': {'category': cat, 'status': status, 'crop': crop_id, 'q': q},
    })


def expense_add_view(request):
    initial = {'crop': request.GET.get('crop')} if request.GET.get('crop') else {}
    form = ExpenseForm(request.POST or None, farmer=request.farmer, initial=initial)
    if request.method == 'POST' and form.is_valid():
        exp = form.save(commit=False)
        exp.farmer = request.farmer
        exp.save()
        log_activity(request.farmer, f"Kharcha: {exp.title} - Rs {exp.amount}")
        if exp.payment_status == 'Pending':
            notify(request.farmer, f"Udhaar baaki: Rs {exp.amount}", f"{exp.paid_to or 'Dukaan'} ko {exp.title} ka paisa dena hai.",
                   kind='payment', severity='warning', link='/finance/expenses/?status=Pending')
        messages.success(request, 'Kharcha add ho gaya.')
        return redirect('finance:expenses')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Naya Kharcha Add Karein', 'back_url': 'finance:expenses'})


def expense_edit_view(request, pk):
    exp = get_object_or_404(FarmExpense, pk=pk, farmer=request.farmer)
    if exp.source_operation_id:
        messages.info(request, 'Yeh kharcha kheti ke kaam se bana hai. Isse "Crop Care" me kaam edit karke badlein.')
        return redirect('farms:operation_edit', pk=exp.source_operation_id)
    form = ExpenseForm(request.POST or None, instance=exp, farmer=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kharcha update ho gaya.')
        return redirect('finance:expenses')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Kharcha Edit Karein', 'back_url': 'finance:expenses'})


def expense_delete_view(request, pk):
    exp = get_object_or_404(FarmExpense, pk=pk, farmer=request.farmer)
    if exp.source_operation_id:
        messages.info(request, 'Yeh kharcha kheti ke kaam se juda hai. Kaam delete karne par yeh hat jayega.')
        return redirect('farms:operation_list')
    return confirm_delete(request, exp, 'finance:expenses', f"Kharcha '{exp.title}'")


@require_POST
def expense_mark_paid_view(request, pk):
    exp = get_object_or_404(FarmExpense, pk=pk, farmer=request.farmer)
    exp.payment_status = 'Paid'
    exp.save()
    messages.success(request, f"'{exp.title}' ka payment chukta mark ho gaya.")
    return redirect(request.META.get('HTTP_REFERER') or 'finance:expenses')


# ------------------------------------------------------------------ SALES
def sale_list_view(request):
    qs = FarmSale.objects.filter(farmer=request.farmer).select_related('crop')
    crop_id, status = request.GET.get('crop', ''), request.GET.get('status', '')
    if crop_id.isdigit():
        qs = qs.filter(crop_id=crop_id)
    if status:
        qs = qs.filter(payment_status=status)
    agg = qs.aggregate(rev=Sum('total_amount'), rec=Sum('amount_received'), qty=Sum('quantity_quintals'))
    page, querystring = paginate(request, qs, 15)
    stock_crops = [c for c in Crop.objects.filter(land__farmer=request.farmer, actual_yield_quintal__gt=0)
                   if c.remaining_stock() > 0]
    return render(request, 'sale_list.html', {
        'page': page, 'qs': querystring, 'revenue': _d(agg['rev']), 'received': _d(agg['rec']),
        'balance': _d(agg['rev']) - _d(agg['rec']), 'qty': _d(agg['qty']),
        'crops': Crop.objects.filter(land__farmer=request.farmer), 'stock_crops': stock_crops,
        'sel': {'crop': crop_id, 'status': status},
    })


def sale_add_view(request):
    initial = {'crop': request.GET.get('crop')} if request.GET.get('crop') else {}
    form = SaleForm(request.POST or None, farmer=request.farmer, initial=initial)
    if not form.fields['crop'].queryset.exists():
        messages.warning(request, 'Bikri darj karne ke liye pehle kisi fasal ka utpadan (Katayi) darj karein.')
        return redirect('farms:crop_list')
    if request.method == 'POST' and form.is_valid():
        sale = form.save(commit=False)
        sale.farmer = request.farmer
        sale.save()
        log_activity(request.farmer, f"Bikri: {sale.crop.name} {sale.quantity_quintals} Qt - Rs {sale.total_amount}")
        notify(request.farmer, f"Bikri darj: {sale.crop.name} - Rs {sale.total_amount}",
               f"{sale.quantity_quintals} Qt, {sale.buyer_name} ko.", kind='sale', severity='success', link='/finance/sales/')
        if sale.balance > 0:
            notify(request.farmer, f"Paisa baaki: Rs {sale.balance}", f"{sale.buyer_name} se milna hai.",
                   kind='payment', severity='warning', link='/finance/sales/?status=Pending')
        messages.success(request, f"Bikri save ho gayi: Rs {sale.total_amount}")
        return redirect('finance:sales')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Nayi Bikri Darj Karein', 'back_url': 'finance:sales', 'calc': 'sale'})


def sale_edit_view(request, pk):
    sale = get_object_or_404(FarmSale, pk=pk, farmer=request.farmer)
    form = SaleForm(request.POST or None, instance=sale, farmer=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Bikri update ho gayi.')
        return redirect('finance:sales')
    return render(request, 'generic_form.html', {'form': form, 'title': 'Bikri Edit Karein', 'back_url': 'finance:sales', 'calc': 'sale'})


def sale_delete_view(request, pk):
    sale = get_object_or_404(FarmSale, pk=pk, farmer=request.farmer)
    return confirm_delete(request, sale, 'finance:sales', f"Bikri ({sale.buyer_name}, {sale.quantity_quintals} Qt)",
                          'Delete karne par yeh matra wapas stock me jud jayegi.')


@require_POST
def sale_receive_view(request, pk):
    """Vyapari se baaki paisa mila - receive darj karna."""
    sale = get_object_or_404(FarmSale, pk=pk, farmer=request.farmer)
    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except Exception:
        amount = Decimal('0')
    if amount <= 0:
        messages.error(request, 'Sahi rashi daalein.')
    elif amount > sale.balance:
        messages.error(request, f"Baaki rashi sirf Rs {sale.balance} hai.")
    else:
        sale.amount_received += amount
        sale.save()
        log_activity(request.farmer, f"Paisa mila: Rs {amount} ({sale.buyer_name})")
        messages.success(request, f"Rs {amount} mil gaye. Baaki: Rs {sale.balance}")
    return redirect(request.META.get('HTTP_REFERER') or 'finance:sales')


# ------------------------------------------------------------------ REPORTS
def _filtered(request):
    start, end = _parse_date(request.GET.get('from')), _parse_date(request.GET.get('to'))
    crop_id = request.GET.get('crop', '')
    exp = FarmExpense.objects.filter(farmer=request.farmer)
    sal = FarmSale.objects.filter(farmer=request.farmer)
    if start:
        exp, sal = exp.filter(date__gte=start), sal.filter(sale_date__gte=start)
    if end:
        exp, sal = exp.filter(date__lte=end), sal.filter(sale_date__lte=end)
    if crop_id.isdigit():
        exp, sal = exp.filter(crop_id=crop_id), sal.filter(crop_id=crop_id)
    return exp, sal, start, end, crop_id


def reports_view(request):
    exp, sal, start, end, crop_id = _filtered(request)
    income = _d(sal.aggregate(t=Sum('total_amount'))['t'])
    expense = _d(exp.aggregate(t=Sum('amount'))['t'])
    received = _d(sal.aggregate(t=Sum('amount_received'))['t'])

    rows = []
    crops = Crop.objects.filter(land__farmer=request.farmer).select_related('land')
    if crop_id.isdigit():
        crops = crops.filter(pk=crop_id)
    for c in crops:
        c_exp = _d(exp.filter(crop=c).aggregate(t=Sum('amount'))['t'])
        c_rev = _d(sal.filter(crop=c).aggregate(t=Sum('total_amount'))['t'])
        if c_exp or c_rev:
            profit = c_rev - c_exp
            rows.append({'crop': c, 'expense': c_exp, 'revenue': c_rev, 'profit': profit,
                         'per_acre': (profit / c.allocated_acres).quantize(Decimal('0.01')) if c.allocated_acres else 0})

    cat_rows = list(exp.values('category').annotate(total=Sum('amount')).order_by('-total'))
    labels = dict(FarmExpense.CATEGORIES)
    max_cat = max([r['total'] for r in cat_rows], default=1)
    for r in cat_rows:
        r['label'] = labels.get(r['category'], r['category'])
        r['pct'] = int(r['total'] / max_cat * 100)
        r['share'] = int(r['total'] / expense * 100) if expense else 0

    m_exp = {r['m']: float(r['t']) for r in exp.annotate(m=TruncMonth('date')).values('m').annotate(t=Sum('amount'))}
    m_inc = {r['m']: float(r['t']) for r in sal.annotate(m=TruncMonth('sale_date')).values('m').annotate(t=Sum('total_amount'))}
    months = sorted(set(m_exp) | set(m_inc))[-12:]
    chart = {'labels': [m.strftime('%b %Y') for m in months],
             'expense': [m_exp.get(m, 0) for m in months], 'income': [m_inc.get(m, 0) for m in months]}

    return render(request, 'reports.html', {
        'income': income, 'expense': expense, 'profit': income - expense,
        'received': received, 'receivable': income - received,
        'rows': rows, 'cat_rows': cat_rows, 'chart': chart,
        'crops': Crop.objects.filter(land__farmer=request.farmer),
        'sel': {'from': request.GET.get('from', ''), 'to': request.GET.get('to', ''), 'crop': crop_id},
    })


def export_csv_view(request, kind):
    exp, sal, *_ = _filtered(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{kind}.csv"'
    response.write('\ufeff')
    w = csv.writer(response)
    if kind == 'expenses':
        w.writerow(['Date', 'Title', 'Category', 'Crop', 'Paid To', 'Method', 'Status', 'Amount'])
        for e in exp.select_related('crop'):
            w.writerow([e.date, e.title, e.category, e.crop.name if e.crop else '', e.paid_to,
                        e.payment_method, e.payment_status, e.amount])
    else:
        w.writerow(['Date', 'Crop', 'Buyer', 'Place', 'Qty (Qt)', 'Rate', 'Deductions', 'Net Amount', 'Received', 'Status'])
        for s in sal.select_related('crop'):
            w.writerow([s.sale_date, s.crop.name if s.crop else '', s.buyer_name, s.sale_place,
                        s.quantity_quintals, s.price_per_quintal, s.deductions, s.total_amount,
                        s.amount_received, s.payment_status])
    return response
