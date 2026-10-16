from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from farms.models import Crop, Land

from .models import MandiPrice, PestDetection, Scheme
from .services import fetch_live_mandi_rates


def pest_detection_view(request):
    # Sirf logged-in kisan ka apna data (pehle FarmerProfile.objects.first() sabka data dikhata tha)
    history = PestDetection.objects.filter(farmer=request.farmer)[:5]
    return render(request, 'pest-detection.html', {
        'history': history,
        'latest_result': history[0] if history else None,
    })


def market_view(request):
    # Agar user ne 'Sync Live Feeds' par click kiya ho
    if request.GET.get('sync') == 'true':
        state = request.GET.get('state', 'Madhya Pradesh')
        success, msg = fetch_live_mandi_rates(state=state)
        if success:
            messages.success(request, "Current mandi bhav successfully updated from official portal!")
        else:
            messages.warning(request, f"Live fetch notice: {msg}")
        return redirect('ai_services:market')

    # Latest updated price pehle dikhayenge
    mandi_prices = MandiPrice.objects.all().order_by('-updated_at')
    
    context = {
        'mandi_prices': mandi_prices,
    }
    return render(request, 'market.html', context)


def loan_subsidy_view(request):
    farmer = request.farmer
    active_crops = Crop.objects.filter(land__farmer=farmer, is_active=True)
    total_land = Land.objects.filter(farmer=farmer).aggregate(Sum('total_area_acres'))['total_area_acres__sum'] or 0

    # 1. Base Queryset (Saari schemes uthao)
    schemes = Scheme.objects.all()

    # 2. Filters tabhi lagao jab user ne sach me koi value di ho
    search_query = request.GET.get('q', '').strip()
    state_filter = request.GET.get('state', '').strip()
    cat_filter = request.GET.get('category', '').strip()

    if search_query:
        schemes = schemes.filter(title__icontains=search_query)
    if state_filter and "select" not in state_filter.lower():
        schemes = schemes.filter(state__icontains=state_filter)
    if cat_filter and "all" not in cat_filter.lower():
        schemes = schemes.filter(category=cat_filter)

    # 3. Direct Total Counts (Bina filter ke absolute count)
    total_schemes = Scheme.objects.count()
    subsidy_count = Scheme.objects.filter(category__in=['Subsidy', 'Solar', 'Machinery']).count()
    loan_count = Scheme.objects.filter(category='Loan').count()
    insurance_count = Scheme.objects.filter(category='Insurance').count()

    context = {
        'schemes': schemes,
        'total_schemes': total_schemes,
        'subsidy_count': subsidy_count,
        'loan_count': loan_count,
        'insurance_count': insurance_count,
        'search_query': search_query,
        'state_filter': state_filter,
        'cat_filter': cat_filter,
        'total_land': total_land,
        'active_crops': active_crops,
    }
    return render(request, 'loan-subsidy.html', context)

@require_POST
def check_eligibility_view(request):
    scheme_id = request.POST.get('scheme_id')
    land_acres = float(request.POST.get('land_acres', 0) or 0)
    category = request.POST.get('farmer_category', 'general')
    state = request.POST.get('state', '').strip()

    scheme = get_object_or_404(Scheme, id=scheme_id)
    title_lower = scheme.title.lower()

    is_eligible = True
    reasons = []
    required_docs = [
        "Farmer ID / Identity Proof",
        "Land Record (Khasra / B-1 Khatoni Copy)",
        "Active Bank Account Passbook",
        "Passport Size Photos (2)"
    ]

    # Specific Loan Criteria Check
    if "tractor" in title_lower or "machinery" in title_lower:
        if land_acres < 2.0:
            is_eligible = False
            reasons.append("Tractor loan ke liye bank aamtaur par kam se kam 2.0 Acre cultivable land maangte hain.")
        required_docs.append("Dealer Quotation & Proforma Invoice")

    elif "dairy" in title_lower or "animal husbandry" in title_lower:
        required_docs.append("Veterinary Health Certificate of Animals")

    elif "solar" in title_lower:
        if land_acres < 0.5:
            is_eligible = False
            reasons.append("Solar pump installation ke liye kam se kam 0.5 Acre zameen avashyak hai.")
        required_docs.append("Electricity Connection No-Dues Undertaking")

    elif "warehouse" in title_lower or "aif" in title_lower:
        required_docs.append("Detailed Project Report (DPR) & Site Map")

    elif "kcc" in title_lower:
        required_docs.append("No-Dues Certificate from local banks")

    if is_eligible:
        message = f"Badhai ho! Aap '{scheme.title}' ke patra hain."
    else:
        message = "Khed hai, vartaman me aap is loan program ke criteria ko match nahi karte."

    return JsonResponse({
        'eligible': is_eligible,
        'scheme_title': scheme.title,
        'message': message,
        'reasons': reasons,
        'required_docs': required_docs,
        'apply_link': scheme.official_link or '#'
    })