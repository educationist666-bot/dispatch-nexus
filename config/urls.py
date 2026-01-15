from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Public
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # App
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-clients/', views.manage_clients, name='manage_clients'),
    path('super-admin/', views.manage_clients, name='super_admin_desk'), # Alias for your HTML

    # Placeholders
    path('fleet/', views.manage_fleet, name='manage_fleet'),
    path('loads/', views.add_load, name='add_load'),
    path('docs/', views.document_center, name='document_center'),
    path('settings/', views.company_settings, name='company_settings'),
    path('plans/', views.subscription_plans, name='subscription_plans'),
]