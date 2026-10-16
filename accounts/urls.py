from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledAuthForm

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html', authentication_form=StyledAuthForm,
        redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('leaving/', views.leaving_view, name='leaving'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('documents/add/', views.document_add_view, name='document_add'),
    path('documents/<int:pk>/edit/', views.document_edit_view, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete_view, name='document_delete'),
]
