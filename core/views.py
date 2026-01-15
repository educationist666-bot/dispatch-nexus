from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import Driver, Load, UserProfile, Company
from .forms import LoadForm, DriverForm, RegistrationForm, OnboardingDocForm, PaymentReceiptForm, CompanyDocForm

# --- PUBLIC ---
def home(request): return render(request, 'home.html')
def public_plans(request): return render(request, 'public_plans.html')
def contact_us(request): return render(request, 'contact_us.html')
def refund_policy(request): return render(request, 'refund_policy.html')
def portal_choice(request): return render(request, 'portal_choice.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            company_name = form.cleaned_data['company_name']
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username taken.")
                return render(request, 'register.html', {'form': form})
            u = User.objects.create_user(username=username, email=email, password=password)
            c = Company.objects.create(name=company_name, owner=u)
            c.dot_number = form.cleaned_data.get('dot_number', '')
            c.phone = form.cleaned_data.get('phone', '')
            c.save()
            UserProfile.objects.create(user=u, company=c, role='admin')
            login(request, u)
            return redirect('onboarding_docs')
    return render(request, 'register.html', {'form': RegistrationForm()})

# --- ONBOARDING & PAYMENTS ---
@login_required
def onboarding_docs(request):
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if request.method == 'POST':
        if request.FILES.get('mc_cert'): c.mc_cert = request.FILES['mc_cert']
        if request.FILES.get('insurance_cert'): c.insurance_cert = request.FILES['insurance_cert']
        if request.FILES.get('w9_cert'): c.w9_cert = request.FILES['w9_cert']
        form = OnboardingDocForm(request.POST, instance=c)
        if form.is_valid(): form.save(); c.save(); return redirect('subscription_plans')
    return render(request, 'onboarding_docs.html', {'form': OnboardingDocForm(instance=c)})

@login_required
def subscription_plans(request): return render(request, 'subscription_plans.html')

@login_required
def process_payment(request):
    c = request.user.userprofile.company
    if 'plan' in request.GET: c.plan_type = request.GET['plan']; c.save()
    if request.method == 'POST':
        if request.FILES.get('payment_receipt'):
            c.payment_receipt = request.FILES['payment_receipt']
            c.payment_submitted_at = timezone.now()
            c.is_active = False
            c.save()
            return render(request, 'payment_pending.html')
    return render(request, 'payment_upload.html', {'form': PaymentReceiptForm(), 'company': c})

# --- HQ ADMIN ---
@user_passes_test(lambda u: u.is_superuser)
def super_admin_desk(request):
    # Fetch lists
    pending = Company.objects.filter(is_active=False).exclude(payment_submitted_at__isnull=True)
    active = Company.objects.filter(is_active=True)
    
    # 1. Calculate Total Clients
    total_clients = active.count()
    
    # 2. Calculate MRR (Monthly Recurring Revenue)
    # Match these strings to your choice in subscription_plans.html
    plan_prices = {
        'starter': 99,
        'pro': 199,
        'enterprise': 499
    }
    
    mrr = 0
    for company in active:
        # Normalize plan name to lowercase to match dictionary keys
        plan_name = str(company.plan_type).lower()
        mrr += plan_prices.get(plan_name, 0)

    stats = {
        'total_clients': total_clients,
        'mrr': mrr,
        'pending_count': pending.count(),
        'total_companies': Company.objects.count()
    }

    return render(request, 'super_admin_desk.html', {
        'pending': pending, 
        'active': active, 
        'stats': stats
    })

@user_passes_test(lambda u: u.is_superuser)
def approve_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.subscription_end_date = timezone.now() + timedelta(days=30); c.is_active = True; c.save()
    return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def pause_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.is_active = False; c.save(); return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def delete_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.owner.delete(); return redirect('super_admin_desk')

# --- DASHBOARD (UPDATED STATUS LOGIC) ---
@login_required
def dashboard(request):
    if request.user.is_superuser: return redirect('super_admin_desk')
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if not c.has_access: return redirect('subscription_plans')
    
    drivers = Driver.objects.filter(company=c)
    loads = Load.objects.filter(company=c).exclude(status='paid')
    
    schedule = []
    for d in drivers:
        # Get active load
        fl = Load.objects.filter(driver=d).exclude(status='paid').order_by('-delivery_date').first()
        
        status_label = "Available"
        next_avail = "Ready Now"
        
        if fl:
            # Map database status to readable label
            if fl.status == 'booked': status_label = "Booked"
            elif fl.status == 'active': status_label = "In Transit"
            elif fl.status == 'delivered': status_label = "Delivered"
            
            # If delivered, they might be free soon, but technically still on the load until paid/cleared
            if fl.status == 'delivered':
                 next_avail = "Unloading Complete"
            else:
                 next_avail = f"{fl.destination} @ {fl.delivery_date.strftime('%b %d, %H:%M')}"

        schedule.append({
            'unit': d.truck_number, 
            'driver': d.name, 
            'status_label': status_label,
            'next_available': next_avail
        })

    is_starter = (str(c.plan_type).lower() == 'starter')
    show_profit = not is_starter
    stats = {'revenue': sum(l.rate for l in loads), 'profit': sum(l.net_profit for l in loads), 'drivers': drivers.count()}
    return render(request, 'dashboard.html', {'stats': stats, 'active_loads': loads, 'schedule': schedule, 'company': c, 'show_profit': show_profit})

# --- NEW: MANAGE LOADS (STATUS UPDATER) ---
@login_required
def manage_loads(request):
    c = request.user.userprofile.company
    # Fetch all active loads (not paid ones)
    loads = Load.objects.filter(company=c).exclude(status='paid').order_by('-pickup_date')
    
    if request.method == 'POST':
        load_id = request.POST.get('load_id')
        new_status = request.POST.get('new_status')
        l = get_object_or_404(Load, id=load_id, company=c)
        l.status = new_status
        l.save()
        messages.success(request, f"Load {l.load_ref} status updated to {new_status}!")
        return redirect('manage_loads')
        
    return render(request, 'manage_loads.html', {'loads': loads})

@login_required
def manage_fleet(request):
    c = request.user.userprofile.company
    drivers = Driver.objects.filter(company=c)
    if request.method == 'POST':
        is_starter = (str(c.plan_type).lower() == 'starter')
        if is_starter and drivers.count() >= 3: messages.error(request, "STARTER PLAN LIMIT REACHED: Upgrade to add more units.")
        else:
            d = Driver(company=c)
            d.name = request.POST.get('name'); d.phone = request.POST.get('phone')
            d.truck_number = request.POST.get('truck_number'); d.status = request.POST.get('status')
            if request.FILES.get('cdl_file'): d.cdl_file = request.FILES['cdl_file']
            if request.FILES.get('medical_card_file'): d.medical_card_file = request.FILES['medical_card_file']
            d.save(); messages.success(request, "Unit added!")
            return redirect('manage_fleet')
    return render(request, 'manage_fleet.html', {'drivers': drivers, 'company': c})

@login_required
def add_load(request):
    c = request.user.userprofile.company
    if request.method == 'POST':
        form = LoadForm(c, request.POST, request.FILES) 
        if form.is_valid():
            l = form.save(commit=False); l.company = c; l.save()
            messages.success(request, "Load Booked!")
            return redirect('manage_loads') # Redirect to the new Manage Loads page
        else:
            for field, errors in form.errors.items():
                for error in errors: messages.error(request, f"Error in {field}: {error}")
    else: form = LoadForm(c)
    return render(request, 'add_load.html', {'form': form})

@login_required
def edit_load(request, load_id):
    l = get_object_or_404(Load, id=load_id)
    if request.method == 'POST':
        form = LoadForm(l.company, request.POST, request.FILES, instance=l)
        if form.is_valid(): form.save(); return redirect('manage_loads')
    else: form = LoadForm(l.company, instance=l)
    return render(request, 'edit_load.html', {'form': form})

@login_required
def manage_clients(request):
    c = request.user.userprofile.company
    if request.method == 'POST':
        u_name = request.POST.get('username')
        u_pass = request.POST.get('password')
        if User.objects.filter(username=u_name).exists(): messages.error(request, "Username taken")
        else:
            u = User.objects.create_user(username=u_name, password=u_pass)
            UserProfile.objects.create(user=u, company=c, role='owner')
            messages.success(request, f"Owner {u_name} created!")
    owners = UserProfile.objects.filter(company=c, role='owner')
    return render(request, 'manage_clients.html', {'company': c, 'owners': owners})

@login_required
def complete_load(request, load_id):
    l = get_object_or_404(Load, id=load_id); l.status='delivered'; l.save(); return redirect('manage_loads')

@login_required
def generate_invoice(request, load_id):
    l = get_object_or_404(Load, id=load_id); return render(request, 'invoice.html', {'load': l, 'company': l.company})

@login_required
def company_settings(request):
    c=request.user.userprofile.company; form=CompanyDocForm(request.POST, instance=c)
    if request.method=='POST' and form.is_valid(): form.save(); return redirect('dashboard')
    return render(request, 'company_settings.html', {'form': CompanyDocForm(instance=c), 'company': c})

@login_required
def document_center(request):
    c = request.user.userprofile.company
    drivers = Driver.objects.filter(company=c); loads = Load.objects.filter(company=c)
    return render(request, 'document_center.html', {'company': c, 'drivers': drivers, 'loads': loads})

@login_required
def client_dashboard(request): return render(request, 'client_dashboard.html')
def custom_logout(request): logout(request); return redirect('home')