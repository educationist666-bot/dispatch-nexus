from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from .models import Company, UserProfile, Truck, Load, Driver

# --- 1. PUBLIC PAGES ---

def home(request):
    """The Marketing Home Page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html') # You need an index.html

def register(request):
    """
    Handles Company Registration + Subscription Selection.
    New companies are NOT approved by default.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name')
        plan = request.POST.get('plan') # starter, pro, etc.

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username taken.")
            return redirect('register')

        # 1. Create User (Owner)
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 2. Create Company (Not Approved yet)
        company = Company.objects.create(owner=user, name=company_name, plan_type=plan, is_approved=False)
        
        # 3. Create Profile linked to Company
        UserProfile.objects.create(user=user, company=company, role='dispatcher')

        # 4. Log them in automatically
        login(request, user)
        return redirect('dashboard')

    return render(request, 'registration/register.html')

# --- 2. PROTECTED SYSTEM ---

@login_required
def dashboard(request):
    user = request.user
    
    # SAFETY CHECK: Does user have a profile?
    if not hasattr(user, 'profile'):
        return render(request, 'error.html', {'message': 'No profile found.'})
    
    profile = user.profile
    company = profile.company

    # CHECK 1: Is this the HQ Admin (Superuser)?
    if user.is_superuser:
        # HQ View: See all companies waiting for approval
        pending_companies = Company.objects.filter(is_approved=False)
        return render(request, 'hq_dashboard.html', {'pending': pending_companies})

    # CHECK 2: Is the Company Approved?
    if not company.is_approved:
        return render(request, 'pending_approval.html')

    # --- NORMAL DISPATCHER DASHBOARD (ISOLATED DATA) ---
    # We filter EVERYTHING by 'company=company'
    # This ensures they NEVER see another company's data
    trucks = Truck.objects.filter(company=company)
    active_loads = Load.objects.filter(company=company, status='active')
    
    context = {
        'company': company,
        'stats': {
            'revenue': 0, # Add calculation logic here
            'drivers': trucks.count(),
        },
        'active_loads': active_loads,
        'schedule': trucks # Simplification for template
    }
    return render(request, 'dashboard.html', context)

@login_required
def manage_clients(request):
    """
    Owner Login Creation:
    Dispatchers can create sub-users (Owners) for THEIR company only.
    """
    profile = request.user.profile
    company = profile.company
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Create user
        new_user = User.objects.create_user(username=username, password=password)
        
        # Link to SAME company
        UserProfile.objects.create(user=new_user, company=company, role='owner')
        
        messages.success(request, f"Owner {username} created for {company.name}")
        return redirect('manage_clients')

    # Show only users in THIS company
    company_users = UserProfile.objects.filter(company=company)
    return render(request, 'manage_clients.html', {'clients': company_users})

# --- PLACEHOLDERS TO PREVENT CRASHES ---
@login_required
def manage_fleet(request): return render(request, 'dashboard.html')
@login_required
def add_load(request): return render(request, 'dashboard.html')
@login_required
def document_center(request): return render(request, 'dashboard.html')
@login_required
def company_settings(request): return render(request, 'dashboard.html')
@login_required
def subscription_plans(request): return render(request, 'dashboard.html')