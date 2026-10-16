from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('<int:pk>/read/', views.mark_read_view, name='read'),
    path('read-all/', views.mark_all_read_view, name='read_all'),
    path('<int:pk>/delete/', views.delete_view, name='delete'),
    path('clear-read/', views.clear_read_view, name='clear_read'),
    path('refresh/', views.refresh_view, name='refresh'),
    path('api/summary/', views.api_summary_view, name='api_summary'),

    path('reminders/', views.reminder_list_view, name='reminders'),
    path('reminders/add/', views.reminder_add_view, name='reminder_add'),
    path('reminders/<int:pk>/edit/', views.reminder_edit_view, name='reminder_edit'),
    path('reminders/<int:pk>/delete/', views.reminder_delete_view, name='reminder_delete'),
    path('reminders/<int:pk>/toggle/', views.reminder_toggle_view, name='reminder_toggle'),
]
