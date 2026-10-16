import time

from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .middleware import LEAVE_KEY

from notifications.services import notify

from .forms import DocumentForm, ProfileForm, SignupForm
from .models import FarmerDocument
from .utils import confirm_delete, log_activity


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('farms:dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        notify(user.farmer_profile, 'Swagat hai! Smart Farming me aapka account ban gaya',
               'Sabse pehle apna Khet (Land) add karein, phir fasal ki buwai log karein.',
               kind='system', severity='success', link='/lands/add/')
        messages.success(request, 'Account ban gaya! Ab apna pehla khet add karein.')
        return redirect('farms:land_add')
    return render(request, 'registration/signup.html', {'form': form})


def profile_view(request):
    farmer = request.farmer
    from farms.models import Crop, Land
    context = {
        'profile': farmer,
        'documents': farmer.documents.all(),
        'activities': farmer.activities.all()[:10],
        'land_count': Land.objects.filter(farmer=farmer).count(),
        'crop_count': Crop.objects.filter(land__farmer=farmer).count(),
    }
    return render(request, 'profile.html', context)


def profile_edit_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.farmer)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(request.farmer, 'Profile update kiya')
        messages.success(request, 'Profile update ho gayi.')
        return redirect('accounts:profile')
    return render(request, 'generic_form.html', {
        'form': form, 'title': 'Profile Edit Karein', 'back_url': 'accounts:profile', 'multipart': True})


def document_add_view(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.farmer = request.farmer
        doc.save()
        log_activity(request.farmer, f"Document add kiya: {doc.title}")
        messages.success(request, 'Document save ho gaya.')
        return redirect('accounts:profile')
    return render(request, 'generic_form.html', {
        'form': form, 'title': 'Naya Document Add Karein', 'back_url': 'accounts:profile', 'multipart': True})


def document_edit_view(request, pk):
    doc = get_object_or_404(FarmerDocument, pk=pk, farmer=request.farmer)
    form = DocumentForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Document update ho gaya.')
        return redirect('accounts:profile')
    return render(request, 'generic_form.html', {
        'form': form, 'title': f'Document Edit: {doc.title}', 'back_url': 'accounts:profile', 'multipart': True})


def document_delete_view(request, pk):
    doc = get_object_or_404(FarmerDocument, pk=pk, farmer=request.farmer)
    return confirm_delete(request, doc, 'accounts:profile', f"Document '{doc.title}'")



@require_POST
def leaving_view(request):
    """
    Browser (navigator.sendBeacon) tab/window band hote waqt yahan POST karta hai.
    Hum sirf time mark karte hain; agar user kuch second me wapas nahi aata
    (middleware dekhta hai) to session logout ho jaata hai.
    action=stay  -> marker hata do (user wapas aa gaya / tab dobara focus hua)
    """
    if request.user.is_authenticated:
        if request.POST.get('action') == 'stay':
            request.session.pop(LEAVE_KEY, None)
        else:
            request.session[LEAVE_KEY] = time.time()
    return HttpResponse(status=204)
