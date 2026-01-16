from django.contrib import admin
from django.urls import path, include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- PUBLIC PAGES ---
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('plans/', views.public_plans, name='plans'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('refund-policy/', views.refund_policy, name='refund_policy'), # <--- THIS LINE WAS MISSING
    path('portal/', views.portal_choice, name='portal_choice'),
    
    # --- SAAS & PAYMENTS ---
    path('onboarding/docs/', views.onboarding_docs, name='onboarding_docs'),
    path('subscription/', views.subscription_plans, name='subscription_plans'),
    path('pay/', views.process_payment, name='process_payment'),
    
    # --- HQ ADMIN CONTROL ---
    path('nexus-hq-control/', views.super_admin_desk, name='super_admin_desk'),
    path('hq/approve/<int:company_id>/', views.approve_company, name='approve_company'),
    path('hq/pause/<int:company_id>/', views.pause_company, name='pause_company'),
    path('hq/delete/<int:company_id>/', views.delete_company, name='delete_company'),
    path('hq/edit-access/<int:company_id>/', views.edit_access_days, name='edit_access_days'),
    
    # --- DISPATCHER DASHBOARD ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manage-loads/', views.manage_loads, name='manage_loads'),
    path('manage-fleet/', views.manage_fleet, name='manage_fleet'),
    path('add-load/', views.add_load, name='add_load'),
    path('edit-load/<int:load_id>/', views.edit_load, name='edit_load'),
    path('complete-load/<int:load_id>/', views.complete_load, name='complete_load'),
    path('invoice/<int:load_id>/', views.generate_invoice, name='generate_invoice'),
    path('company-settings/', views.company_settings, name='company_settings'),
    path('documents/', views.document_center, name='document_center'),
    path('manage-clients/', views.manage_clients, name='manage_clients'),
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)