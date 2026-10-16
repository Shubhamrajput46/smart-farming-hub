from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    path('pest-detection/', views.pest_detection_view, name='pest_detection'),
    path('market/', views.market_view, name='market'),
    path('loan-subsidy/', views.loan_subsidy_view, name='loan_subsidy'),
    path('check-eligibility/', views.check_eligibility_view, name='check_eligibility'),  # <-- Yeh naya endpoint
]