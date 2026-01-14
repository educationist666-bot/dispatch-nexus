from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages # Added for error messages
from .models import Driver, Load, UserProfile, Company
from .forms import LoadForm, DriverForm, RegistrationForm, OnboardingDocForm, PaymentReceiptForm, CompanyDocForm

# --- PUBLIC PAGES ---
def home(request): return render(request, 'home.html')
def portal_choice(request): return render(request, 'portal_choice.html')
def plans(request): return render(request, 'public_plans.html')
def refund_policy(request): return render(request, 'refund_policy.html')
def contact_us(request): return render(request, 'contact_us.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            u = User.objects.create_user(username=form.cleaned_data['username'], email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            c = Company.objects.create(name=form.cleaned_data['company_name'], owner=u, dot_number=form.cleaned_data['dot_number'], phone=form.cleaned_data['phone'], address=form.cleaned_data['address'], city=form.cleaned_data['city'], state=form.cleaned_data['state'], zip_code=form.cleaned_data['zip_code'])
            p = u.userprofile; p.company = c; p.role = 'admin'; p.save()
            login(request, u)
            return redirect('onboarding_docs')
    return render(request, 'register.html', {'form': RegistrationForm()})

# --- SaaS GATES ---
@login_required
def onboarding_docs(request):
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if c is None: return redirect('register')
    if request.method == 'POST':
        form = OnboardingDocForm(request.POST, request.FILES, instance=c)
        if form.is_valid(): form.save(); return redirect('subscription_plans')
    return render(request, 'onboarding_docs.html', {'form': OnboardingDocForm(instance=c)})

@login_required
def subscription_plans(request): return render(request, 'subscription_plans.html')

@login_required
def process_payment(request):
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if c is None: return redirect('register')
    if 'plan' in request.GET: c.plan_type = request.GET['plan']; c.save()
    if request.method == 'POST':
        form = PaymentReceiptForm(request.POST, request.FILES, instance=c)
        if form.is_valid():
            o = form.save(commit=False); o.payment_submitted_at = timezone.now(); o.is_active = False; o.save()
            return render(request, 'payment_pending.html')
    return render(request, 'payment_upload.html', {'form': PaymentReceiptForm(), 'company': c})

# --- SECRET HQ (UPDATED WITH PAUSE/DELETE) ---
@user_passes_test(lambda u: u.is_superuser)
def super_admin_desk(request):
    pending = Company.objects.filter(is_active=False).exclude(payment_receipt='')
    active = Company.objects.filter(is_active=True).order_by('subscription_end_date')
    revenue = sum(c.plan_type == 'pro' and 80 or (c.plan_type == 'enterprise' and 100 or 25) for c in active)
    
    return render(request, 'super_admin_desk.html', {
        'pending': pending, 'active': active, 
        'total_active': active.count(), 'revenue': revenue
    })

@user_passes_test(lambda u: u.is_superuser)
def approve_company(request, company_id):
    c = get_object_or_404(Company, id=company_id)
    c.subscription_end_date = timezone.now() + timedelta(days=30); c.is_active = True; c.save()
    return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def pause_company(request, company_id):
    c = get_object_or_404(Company, id=company_id)
    c.is_active = False # Locks them out
    c.save()
    return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def delete_company(request, company_id):
    c = get_object_or_404(Company, id=company_id)
    # Delete the user account associated with the company to fully clean up
    c.owner.delete() 
    # Company is auto-deleted because of CASCADE
    return redirect('super_admin_desk')

# --- DASHBOARD & LIMITS ---
@login_required
def dashboard(request):
    if request.user.is_superuser: return redirect('super_admin_desk')
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if c is None: return redirect('register')
    if not c.has_access: return redirect('subscription_plans')
    
    drivers = Driver.objects.filter(company=c)
    loads = Load.objects.filter(company=c).exclude(status='paid')
    
    schedule = []
    for d in drivers:
        fl = Load.objects.filter(driver=d).order_by('-delivery_date').first()
        status = "🟢 Free Now"
        if fl and fl.delivery_date > timezone.now():
            status = f"🔴 Busy until {fl.delivery_date.strftime('%b %d @ %H:%M')}"
        schedule.append({'unit': d.truck_number, 'driver': d.name, 'availability': status, 'location': fl.destination if fl else "Home", 'type': d.get_truck_type_display()})

    # HIDE PROFIT FOR STARTER PLAN
    show_profit = True
    if c.plan_type == 'starter': show_profit = False

    stats = {'revenue': sum(l.rate for l in loads), 'profit': sum(l.net_profit for l in loads), 'drivers': drivers.count()}
    return render(request, 'dashboard.html', {'stats': stats, 'active_loads': loads, 'schedule': schedule, 'company': c, 'show_profit': show_profit})

@login_required
def manage_fleet(request):
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if c is None: return redirect('register')

    if request.method == 'POST':
        # ENFORCE PLAN LIMITS
        current_count = Driver.objects.filter(company=c).count()
        limit_reached = False
        
        if c.plan_type == 'starter' and current_count >= 3: limit_reached = True
        if c.plan_type == 'pro' and current_count >= 10: limit_reached = True
        
        if limit_reached:
            # Show error and don't save
            messages.error(request, f"Upgrade Plan! Your {c.plan_type.title()} plan limit is reached.")
        else:
            form = DriverForm(request.POST, request.FILES)
            if form.is_valid():
                d = form.save(commit=False); d.company = c; d.save()
                return redirect('manage_fleet')
                
    return render(request, 'manage_fleet.html', {'drivers': Driver.objects.filter(company=c), 'form': DriverForm()})

# (Keep other views same as before: company_settings, add_load, etc.)
@login_required
def company_settings(request):
    c = request.user.userprofile.company
    if request.method == 'POST':
        form = CompanyDocForm(request.POST, request.FILES, instance=c)
        if form.is_valid(): form.save(); return redirect('dashboard')
    return render(request, 'company_settings.html', {'form': CompanyDocForm(instance=c), 'company': c})

@login_required
def add_load(request):
    c = request.user.userprofile.company
    if request.method == 'POST':
        form = LoadForm(c, request.POST, request.FILES)
        if form.is_valid(): l = form.save(commit=False); l.company = c; l.save(); return redirect('dashboard')
    return render(request, 'add_load.html', {'form': LoadForm(c)})

def custom_logout(request): logout(request); return redirect('home')
@login_required
def generate_invoice(request, load_id): return redirect('dashboard')
@login_required
def complete_load(request, load_id): l = get_object_or_404(Load, id=load_id, company=request.user.userprofile.company); l.status = 'delivered'; l.save(); return redirect('dashboard')
@login_required
def edit_load(request, load_id): 
    l = get_object_or_404(Load, id=load_id, company=request.user.userprofile.company)
    if request.method == 'POST':
        form = LoadForm(l.company, request.POST, request.FILES, instance=l)
        if form.is_valid(): form.save(); return redirect('dashboard')
    return render(request, 'edit_load.html', {'form': LoadForm(l.company, instance=l), 'load': l})
@login_required
def delete_load(request, load_id): return redirect('dashboard')
@login_required
def manage_clients(request): return redirect('dashboard')
@login_required
def document_center(request): return render(request, 'document_center.html', {'company': request.user.userprofile.company, 'loads': Load.objects.filter(company=request.user.userprofile.company)})