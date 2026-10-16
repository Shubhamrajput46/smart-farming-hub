from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import confirm_delete, log_activity, paginate
from finance.models import FarmExpense, FarmSale
from notifications.models import Reminder
from notifications.services import notify, run_alerts_if_due

from .forms import CropForm, CropOperationForm, HarvestForm, LandForm
from .models import Crop, CropOperationLog, Land

def _crops(request):
    return Crop.objects.filter(land__farmer=request.farmer).select_related('land')


def _estimated_revenue(crops):
    """Khadi fasal ka andaza: anumaanit utpadan x latest mandi bhav (agar mile)."""
    from ai_services.models import MandiPrice
    total, missing = Decimal('0'), 0
    for crop in crops:
        key = crop.name.split()[0] if crop.name else ''
        price = MandiPrice.objects.filter(crop_name__icontains=key).order_by('-updated_at').first() if key else None
        if price and crop.expected_yield_quintal:
            total += crop.expected_yield_quintal * price.today_price
        elif crop.expected_yield_quintal:
            missing += 1
    return total, missing


# ------------------------------------------------------------------ HOME (index.html)
def home_view(request):
    """Project start hote hi sabse pehle landing page (index.html) khulta hai."""
    return render(request, 'index.html')


# ------------------------------------------------------------------ DASHBOARD
def dashboard_view(request):
    farmer = request.farmer
    run_alerts_if_due(request, farmer)
    today = timezone.localdate()

    lands = Land.objects.filter(farmer=farmer)
    active_crops = _crops(request).filter(is_active=True)
    expenses = FarmExpense.objects.filter(farmer=farmer)
    sales = FarmSale.objects.filter(farmer=farmer)

    total_land = lands.aggregate(t=Sum('total_area_acres'))['t'] or Decimal('0')
    total_sown = active_crops.aggregate(t=Sum('allocated_acres'))['t'] or Decimal('0')
    total_expense = expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_income = sales.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
    total_received = sales.aggregate(t=Sum('amount_received'))['t'] or Decimal('0')
    payable = expenses.filter(payment_status='Pending').aggregate(t=Sum('amount'))['t'] or Decimal('0')
    est_revenue, missing_rates = _estimated_revenue(active_crops)

    context = {
        'lands_count': lands.count(),
        'active_crops': active_crops,
        'total_land': total_land,
        'total_sown': total_sown,
        'free_land': total_land - total_sown,
        'total_expense': total_expense,
        'total_income': total_income,
        'net_profit': total_income - total_expense,
        'receivable': total_income - total_received,
        'payable': payable,
        'est_revenue': est_revenue,
        'missing_rates': missing_rates,
        'recent_operations': CropOperationLog.objects.filter(crop__land__farmer=farmer).select_related('crop')[:6],
        'todo_reminders': Reminder.objects.filter(farmer=farmer, is_done=False, due_date__lte=today + timezone.timedelta(days=3))[:5],
        'harvest_soon': active_crops.filter(expected_harvest_date__lte=today + timezone.timedelta(days=15)).order_by('expected_harvest_date')[:4],
        'in_stock': [c for c in _crops(request).filter(actual_yield_quintal__gt=0) if c.remaining_stock() > 0][:4],
    }
    return render(request, 'farming_dashboard.html', context)


# ------------------------------------------------------------------ LAND
def land_list_view(request):
    lands = Land.objects.filter(farmer=request.farmer).annotate(crop_count=Count('crops'))
    return render(request, 'land_list.html', {
        'lands': lands,
        'total_area': sum(l.total_area_acres for l in lands),
    })


def land_add_view(request):
    form = LandForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        land = form.save(commit=False)
        land.farmer = request.farmer
        land.save()
        log_activity(request.farmer, f"Naya khet add kiya: {land.title}")
        messages.success(request, f"Khet '{land.title}' add ho gaya! Ab fasal ki buwai log karein.")
        return redirect('farms:land_detail', pk=land.pk)
    return render(request, 'generic_form.html', {'form': form, 'title': 'Naya Khet Add Karein', 'back_url': 'farms:land_list'})


def land_detail_view(request, pk):
    land = get_object_or_404(Land, pk=pk, farmer=request.farmer)
    return render(request, 'land_detail.html', {
        'land': land,
        'crops': land.crops.all(),
        'sown': land.sown_acres(),
        'available': land.available_area(),
    })


def land_edit_view(request, pk):
    land = get_object_or_404(Land, pk=pk, farmer=request.farmer)
    form = LandForm(request.POST or None, instance=land)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Khet ki details update ho gayi.')
        return redirect('farms:land_detail', pk=land.pk)
    return render(request, 'generic_form.html', {'form': form, 'title': f'Khet Edit: {land.title}', 'back_url': 'farms:land_list'})


def land_delete_view(request, pk):
    land = get_object_or_404(Land, pk=pk, farmer=request.farmer)
    n = land.crops.count()
    warn = f"Is khet ki {n} fasal aur unke saare kaam (operations) bhi delete ho jayenge. Kharcha/Bikri ke record bache rahenge." if n else ''
    return confirm_delete(request, land, 'farms:land_list', f"Khet '{land.title}'", warn)


# ------------------------------------------------------------------ CROP
def crop_list_view(request):
    status = request.GET.get('status', 'active')
    q = request.GET.get('q', '').strip()
    crops = _crops(request)
    if status == 'active':
        crops = crops.filter(is_active=True)
    elif status == 'completed':
        crops = crops.filter(is_active=False)
    if q:
        crops = crops.filter(Q(name__icontains=q) | Q(land__title__icontains=q))
    page, qs = paginate(request, crops, 12)
    return render(request, 'crop_list.html', {'page': page, 'qs': qs, 'status': status, 'q': q})


def crop_add_view(request):
    if not Land.objects.filter(farmer=request.farmer).exists():
        messages.warning(request, 'Pehle apna khet add karein, phir fasal boyein.')
        return redirect('farms:land_add')
    initial = {'land': request.GET.get('land')} if request.GET.get('land') else {}
    form = CropForm(request.POST or None, farmer=request.farmer, initial=initial)
    if request.method == 'POST' and form.is_valid():
        crop = form.save()
        log_activity(request.farmer, f"Nayi fasal boyi: {crop.name} ({crop.allocated_acres} Acre)")
        notify(request.farmer, f"Fasal register: {crop.name}",
               f"{crop.allocated_acres} Acre me buwai. Katayi anumaan: {crop.expected_harvest_date:%d %b %Y}.",
               kind='crop', severity='success', link=f"/crops/{crop.pk}/")
        messages.success(request, f"Fasal '{crop.name}' register ho gayi. Beej ka kharcha 'Kharcha' me add karna na bhulein.")
        return redirect('farms:crop_detail', pk=crop.pk)
    return render(request, 'generic_form.html', {'form': form, 'title': 'Nayi Fasal Ki Buwai Log Karein', 'back_url': 'farms:crop_list'})


def crop_detail_view(request, pk):
    crop = get_object_or_404(_crops(request), pk=pk)
    return render(request, 'crop_detail.html', {
        'crop': crop,
        'operations': crop.operations.all()[:15],
        'expenses': crop.expenses.all()[:10],
        'sales': crop.sales.all()[:10],
        'expense_total': crop.total_expense(),
        'revenue_total': crop.total_revenue(),
        'stages': Crop.STAGE_CHOICES,
    })


def crop_edit_view(request, pk):
    crop = get_object_or_404(_crops(request), pk=pk)
    form = CropForm(request.POST or None, instance=crop, farmer=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Fasal '{crop.name}' update ho gayi.")
        return redirect('farms:crop_detail', pk=crop.pk)
    return render(request, 'generic_form.html', {'form': form, 'title': f'Fasal Edit: {crop.name}', 'back_url': 'farms:crop_list'})


def crop_delete_view(request, pk):
    crop = get_object_or_404(_crops(request), pk=pk)
    warn = (f"Is fasal ke {crop.operations.count()} kheti kaam delete ho jayenge. "
            f"Kharcha/Bikri ke record 'bina fasal' ke bache rahenge.")
    return confirm_delete(request, crop, 'farms:crop_list', f"Fasal '{crop.name}'", warn)


@require_POST
def crop_stage_view(request, pk):
    crop = get_object_or_404(_crops(request), pk=pk)
    stage = request.POST.get('stage')
    valid = [s for s in Crop.STAGE_ORDER if s != 'Completed']
    if stage not in valid:
        messages.error(request, 'Galat stage. Fasal poori karne ke liye "Katayi / Utpadan Darj Karein" use karein.')
    elif stage != crop.stage:
        crop.stage = stage
        crop.save()
        log_activity(request.farmer, f"{crop.name} ki sthiti: {crop.get_stage_display()}")
        notify(request.farmer, f"{crop.name}: ab '{crop.get_stage_display()}'", '', kind='crop', link=f"/crops/{crop.pk}/")
        messages.success(request, f"{crop.name} ki sthiti '{crop.get_stage_display()}' kar di gayi.")
    nxt = request.POST.get('next', '')
    if nxt.startswith('/') and not nxt.startswith('//'):
        return redirect(nxt)
    return redirect('farms:crop_detail', pk=crop.pk)


def crop_harvest_view(request, pk):
    crop = get_object_or_404(_crops(request), pk=pk)
    initial = {
        'actual_yield_quintal': crop.actual_yield_quintal or None,
        'actual_harvest_date': crop.actual_harvest_date or timezone.localdate(),
    }
    form = HarvestForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        crop.actual_yield_quintal = form.cleaned_data['actual_yield_quintal']
        crop.actual_harvest_date = form.cleaned_data['actual_harvest_date']
        crop.stage = 'Completed' if form.cleaned_data['mark_completed'] else 'Harvesting'
        crop.save()
        log_activity(request.farmer, f"Katayi darj: {crop.name} - {crop.actual_yield_quintal} Qt")
        notify(request.farmer, f"Utpadan darj: {crop.name}",
               f"{crop.actual_yield_quintal} Quintal stock me. Ab bikri darj kar sakte hain.",
               kind='stock', severity='success', link=f"/crops/{crop.pk}/")
        messages.success(request, f"{crop.name}: {crop.actual_yield_quintal} Quintal utpadan save ho gaya.")
        return redirect('farms:crop_detail', pk=crop.pk)
    return render(request, 'generic_form.html', {
        'form': form, 'title': f'Katayi / Utpadan Darj: {crop.name}', 'back_url': 'farms:crop_list',
        'hint': f'Anumaanit utpadan tha: {crop.expected_yield_quintal} Quintal'})


# ------------------------------------------------------------------ OPERATIONS (Crop Care)
def operation_list_view(request):
    ops = CropOperationLog.objects.filter(crop__land__farmer=request.farmer).select_related('crop')
    crop_id, op_type = request.GET.get('crop', ''), request.GET.get('type', '')
    if crop_id.isdigit():
        ops = ops.filter(crop_id=crop_id)
    if op_type:
        ops = ops.filter(operation_type=op_type)
    stats = ops.aggregate(cost=Sum('total_cost'), labour=Sum('labour_count'), hours=Sum('hours_run'))
    page, qs = paginate(request, ops, 15)
    return render(request, 'operation_list.html', {
        'page': page, 'qs': qs, 'stats': stats,
        'crops': _crops(request), 'op_types': CropOperationLog.OP_TYPES,
        'sel_crop': crop_id, 'sel_type': op_type,
    })


def operation_add_view(request):
    initial = {'crop': request.GET.get('crop')} if request.GET.get('crop') else {}
    if request.GET.get('type'):
        initial['operation_type'] = request.GET['type']
    form = CropOperationForm(request.POST or None, farmer=request.farmer, initial=initial)
    if request.method == 'POST' and form.is_valid():
        op = form.save()
        log_activity(request.farmer, f"{op.get_operation_type_display()} - {op.crop.name} (Rs {op.total_cost})")
        messages.success(request, 'Kheti ka kaam log ho gaya' + (' aur kharcha ledger me add ho gaya.' if op.total_cost else '.'))
        return redirect('farms:operation_list')
    return render(request, 'generic_form.html', {
        'form': form, 'title': 'Kheti Ka Kaam / Majdoori Log Karein', 'back_url': 'farms:operation_list', 'calc': 'operation'})


def operation_edit_view(request, pk):
    op = get_object_or_404(CropOperationLog, pk=pk, crop__land__farmer=request.farmer)
    form = CropOperationForm(request.POST or None, instance=op, farmer=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kaam update ho gaya (kharcha bhi sync).')
        return redirect('farms:operation_list')
    return render(request, 'generic_form.html', {
        'form': form, 'title': 'Kaam Edit Karein', 'back_url': 'farms:operation_list', 'calc': 'operation'})


def operation_delete_view(request, pk):
    op = get_object_or_404(CropOperationLog, pk=pk, crop__land__farmer=request.farmer)
    return confirm_delete(request, op, 'farms:operation_list', f"Kaam '{op.get_operation_type_display()}' ({op.date})",
                          'Iska judaa hua kharcha bhi ledger se hat jayega.')
