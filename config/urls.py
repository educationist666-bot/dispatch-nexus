from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Auth
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),

    # App
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-clients/', views.manage_clients, name='manage_clients'),
    
    # Placeholders
    path('fleet/', views.manage_fleet, name='manage_fleet'),
    path('loads/', views.add_load, name='add_load'),
    path('docs/', views.document_center, name='document_center'),
    path('settings/', views.company_settings, name='company_settings'),
    path('plans/', views.subscription_plans, name='subscription_plans'),
]