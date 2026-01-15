from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Driver, Truck, Load # Ensure your models are imported correctly

# --- AUTH & DASHBOARD ---

def login_view(request):
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'POST':
        # Registration logic (placeholder - keep your existing if needed)
        pass 
    return render(request, 'registration/register.html')

@login_required
def dashboard(request):
    # 1. Fetch Real Data
    trucks = Truck.objects.all()
    active_loads = Load.objects.filter(status='active')
    
    # 2. Prepare the Schedule List (This feeds the table)
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

    # 3. Stats
    stats = {
        'revenue': 0, 
        'profit': 0,
        'drivers': trucks.count(),
    }

    context = {
        'stats': stats,
        'schedule': schedule_data,
        'active_loads': active_loads,
        # Check if user has a profile and plan_type, handle errors if profile missing
        'show_profit': getattr(request.user, 'profile', None) and request.user.profile.plan_type != 'starter' 
    }
    
    return render(request, 'dashboard.html', context)

# --- CLIENT MANAGEMENT (THE FIX) ---

@login_required
def manage_clients(request):
    # 1. Handle Form Submission (Creating a new Owner)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Simple Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        else:
            try:
                # Create the User
                new_user = User.objects.create_user(username=username, email=email, password=password)
                messages.success(request, f"Owner account '{username}' created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating user: {e}")
            
            return redirect('manage_clients')

    # 2. List Existing Owners (Show all users who are NOT superusers)
    clients = User.objects.filter(is_superuser=False)

    return render(request, 'manage_clients.html', {'clients': clients})

# --- OTHER PLACEHOLDER VIEWS (Keep these to prevent errors) ---

@login_required
def manage_fleet(request):
    # Ensure you have 'manage_fleet.html' or change to 'dashboard.html' temporarily
    return render(request, 'manage_fleet.html') 

@login_required
def document_center(request):
    # Ensure you have 'document_center.html'
    return render(request, 'document_center.html') 

@login_required
def company_settings(request):
    # Ensure you have 'company_settings.html'
    return render(request, 'company_settings.html') 
    
@login_required
def add_load(request):
     return render(request, 'add_load.html') # Placeholder

@login_required
def subscription_plans(request):
     return render(request, 'subscription_plans.html') # Placeholder