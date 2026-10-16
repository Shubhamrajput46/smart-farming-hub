from django.urls import path

from . import views

app_name = 'finance'

urlpatterns = [
    path('expenses/', views.expense_list_view, name='expenses'),
    path('expenses/add/', views.expense_add_view, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit_view, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    path('expenses/<int:pk>/paid/', views.expense_mark_paid_view, name='expense_paid'),

    path('sales/', views.sale_list_view, name='sales'),
    path('sales/add/', views.sale_add_view, name='sale_add'),
    path('sales/<int:pk>/edit/', views.sale_edit_view, name='sale_edit'),
    path('sales/<int:pk>/delete/', views.sale_delete_view, name='sale_delete'),
    path('sales/<int:pk>/receive/', views.sale_receive_view, name='sale_receive'),

    path('reports/', views.reports_view, name='reports'),
    path('reports/export/<str:kind>/', views.export_csv_view, name='export'),
]
