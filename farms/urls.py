from django.urls import path

from . import views

app_name = 'farms'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('lands/', views.land_list_view, name='land_list'),
    path('lands/add/', views.land_add_view, name='land_add'),
    path('lands/<int:pk>/', views.land_detail_view, name='land_detail'),
    path('lands/<int:pk>/edit/', views.land_edit_view, name='land_edit'),
    path('lands/<int:pk>/delete/', views.land_delete_view, name='land_delete'),

    path('crops/', views.crop_list_view, name='crop_list'),
    path('crops/add/', views.crop_add_view, name='crop_add'),
    path('crops/<int:pk>/', views.crop_detail_view, name='crop_detail'),
    path('crops/<int:pk>/edit/', views.crop_edit_view, name='crop_edit'),
    path('crops/<int:pk>/delete/', views.crop_delete_view, name='crop_delete'),
    path('crops/<int:pk>/stage/', views.crop_stage_view, name='crop_stage'),
    path('crops/<int:pk>/harvest/', views.crop_harvest_view, name='crop_harvest'),

    path('crop-care/', views.operation_list_view, name='operation_list'),
    path('crop-care/add/', views.operation_add_view, name='operation_add'),
    path('crop-care/<int:pk>/edit/', views.operation_edit_view, name='operation_edit'),
    path('crop-care/<int:pk>/delete/', views.operation_delete_view, name='operation_delete'),
]
