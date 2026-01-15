from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import logout 
from .models import Driver, Truck, Load, UserProfile 

# --- 1. AUTHENTICATION & HOME ---

def home(request):
    """The landing page helper. Redirects to login or dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def login_view(request):
    """The actual login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'registration/login.html')

def custom_logout(request):
    """Logs the user out safely."""
    logout(request)
    return redirect('login')

def register(request):
    """The registration page."""
    if request.method == 'POST':
        pass # Add logic later
    return render(request, 'registration/register.html')

# --- 2. DASHBOARD ---

@login_required
def dashboard(request):
    # Fetch data safely
    trucks = Truck.objects.all()
    active_loads = Load.objects.filter(status='active')
    
    # Simple stats
    context = {
        'stats': {'revenue': 0, 'profit': 0, 'drivers': trucks.count()},
        'schedule': [], # Keep empty for now to prevent errors
        'active_loads': active_loads,
    }
    return render(request, 'dashboard.html', context)

# --- 3. CLIENT MANAGEMENT ---

@login_required
def manage_clients(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Create user safely
        try:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "User created!")
        except:
            messages.error(request, "Error creating user")
            
    clients = User.objects.filter(is_superuser=False)
    return render(request, 'manage_clients.html', {'clients': clients})

# --- 4. PLACEHOLDERS (To prevent "View Not Found" crashes) ---

@login_required
def manage_fleet(request):
    return render(request, 'dashboard.html') # Redirect to dashboard temporarily

@login_required
def document_center(request):
    return render(request, 'dashboard.html') 

@login_required
def company_settings(request):
    return render(request, 'dashboard.html') 
    
@login_required
def add_load(request):
     return render(request, 'dashboard.html')

@login_required
def subscription_plans(request):
     return render(request, 'dashboard.html')