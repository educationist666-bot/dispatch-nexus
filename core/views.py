from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout 
from .models import Driver, Truck, Load, UserProfile 

# --- NAVIGATION ---

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'registration/login.html')

def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

def register(request):
    if request.method == 'POST':
        pass 
    return render(request, 'registration/register.html')

# --- DASHBOARD ---

@login_required
def dashboard(request):
    trucks = Truck.objects.all()
    active_loads = Load.objects.filter(status='active')
    
    schedule_data = []
    for truck in trucks:
        schedule_data.append({
            'unit': truck.unit_number,
            'driver': truck.driver.name if truck.driver else "Unassigned",
            'type': truck.type,
            'availability': "Available", 
            'location': "Depot",         
            'status': truck.status
        })

    stats = {
        'revenue': 0, 
        'profit': 0,
        'drivers': trucks.count(),
    }

    user_plan = 'starter'
    if hasattr(request.user, 'profile'):
        user_plan = request.user.profile.plan_type

    context = {
        'stats': stats,
        'schedule': schedule_data,
        'active_loads': active_loads,
        'show_profit': user_plan != 'starter' 
    }
    
    return render(request, 'dashboard.html', context)

# --- CLIENT MANAGEMENT ---

@login_required
def manage_clients(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            try:
                new_user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, f"Owner account '{username}' created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating user: {e}")
            return redirect('manage_clients')

    clients = User.objects.filter(is_superuser=False)
    return render(request, 'manage_clients.html', {'clients': clients})

# --- PLACEHOLDERS ---

@login_required
def manage_fleet(request):
    return render(request, 'manage_fleet.html') 

@login_required
def document_center(request):
    return render(request, 'document_center.html') 

@login_required
def company_settings(request):
    return render(request, 'company_settings.html') 
    
@login_required
def add_load(request):
     return render(request, 'add_load.html')

@login_required
def subscription_plans(request):
     return render(request, 'subscription_plans.html')