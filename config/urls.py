from django.contrib import admin
from django.urls import path
from core import views  # Import views from core app

urlpatterns = [
    # 1. Admin Page
    path('admin/', admin.site.urls),

    # 2. Authentication & Home
    path('', views.home, name='home'),  # Matches 'def home' in views.py
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'), # Matches 'def custom_logout'

    # 3. Main App Pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-clients/', views.manage_clients, name='manage_clients'),
    path('manage-fleet/', views.manage_fleet, name='manage_fleet'),
    path('add-load/', views.add_load, name='add_load'),
    path('documents/', views.document_center, name='document_center'),
    path('settings/', views.company_settings, name='company_settings'),
    path('subscription/', views.subscription_plans, name='subscription_plans'),
]