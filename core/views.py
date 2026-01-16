from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import Driver, Load, UserProfile, Company
from .forms import LoadForm, DriverForm, RegistrationForm, OnboardingDocForm, PaymentReceiptForm, CompanyDocForm

# --- AUTH & REGISTRATION ---
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username taken. Please try another.")
                return render(request, 'register.html', {'form': form})
            u = User.objects.create_user(username=username, email=form.cleaned_data['email'], password=form.cleaned_data['password'])
            c = Company.objects.create(name=form.cleaned_data['company_name'], owner=u)
            UserProfile.objects.create(user=u, company=c, role='admin')
            login(request, u)
            return redirect('onboarding_docs')
    return render(request, 'register.html', {'form': RegistrationForm()})

@login_required
def onboarding_docs(request):
    c = request.user.userprofile.company
    if request.method == 'POST':
        form = OnboardingDocForm(request.POST, request.FILES, instance=c)
        if form.is_valid(): form.save(); return redirect('subscription_plans')
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
    return render(request, 'payment_upload.html', {'company': c})

# --- HQ ADMIN ---
@user_passes_test(lambda u: u.is_superuser)
def super_admin_desk(request):
    pending = Company.objects.filter(is_active=False).exclude(payment_submitted_at__isnull=True)
    active = Company.objects.filter(is_active=True)
    plan_prices = {'starter': 99, 'pro': 199, 'enterprise': 499}
    mrr = sum(plan_prices.get(str(c.plan_type).lower(), 0) for c in active)
    stats = {'total_clients': active.count(), 'mrr': mrr, 'pending_count': pending.count()}
    return render(request, 'super_admin_desk.html', {'pending': pending, 'active': active, 'stats': stats})

@user_passes_test(lambda u: u.is_superuser)
def edit_access_days(request, company_id):
    if request.method == 'POST':
        c = get_object_or_404(Company, id=company_id)
        days = int(request.POST.get('days', 0))
        if c.subscription_end_date: c.subscription_end_date += timedelta(days=days)
        else: c.subscription_end_date = timezone.now() + timedelta(days=days)
        c.save(); messages.success(request, f"Access updated for {c.name}")
    return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def approve_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.subscription_end_date = timezone.now() + timedelta(days=30); c.is_active = True; c.save(); return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def pause_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.is_active = False; c.save(); return redirect('super_admin_desk')

@user_passes_test(lambda u: u.is_superuser)
def delete_company(request, company_id):
    c = get_object_or_404(Company, id=company_id); c.owner.delete(); return redirect('super_admin_desk')

# --- DASHBOARD & TOOLS ---
@login_required
def dashboard(request):
    if request.user.is_superuser: return redirect('super_admin_desk')
    try: c = request.user.userprofile.company
    except: return redirect('register')
    if c.payment_submitted_at and not c.is_active: return render(request, 'payment_pending.html')
    if not c.has_access and not c.payment_submitted_at: return redirect('subscription_plans')
    
    drivers = Driver.objects.filter(company=c)
    loads = Load.objects.filter(company=c).exclude(status='paid')
    schedule = []
    for d in drivers:
        fl = Load.objects.filter(driver=d).exclude(status='paid').order_by('-delivery_date').first()
        status_label = "Available"; next_avail = "Ready Now"
        if fl:
            status_label = fl.status.title()
            next_avail = f"{fl.destination} @ {fl.delivery_date.strftime('%b %d, %H:%M')}"
        schedule.append({'unit': d.truck_number, 'driver': d.name, 'status_label': status_label, 'next_available': next_avail})
    stats = {'revenue': sum(l.rate for l in loads), 'profit': sum(l.net_profit for l in loads), 'drivers': drivers.count()}
    return render(request, 'dashboard.html', {'stats': stats, 'company': c, 'schedule': schedule})

@login_required
def manage_loads(request):
    c = request.user.userprofile.company
    if not c.is_active: return render(request, 'payment_pending.html')
    loads = Load.objects.filter(company=c).exclude(status='paid').order_by('-pickup_date')
    if request.method == 'POST':
        l = get_object_or_404(Load, id=request.POST.get('load_id'), company=c)
        l.status = request.POST.get('new_status'); l.save(); return redirect('manage_loads')
    return render(request, 'manage_loads.html', {'loads': loads})

@login_required
def manage_fleet(request):
    c = request.user.userprofile.company
    if not c.is_active: return render(request, 'payment_pending.html')
    drivers = Driver.objects.filter(company=c)
    if request.method == 'POST':
        d = Driver(company=c, name=request.POST.get('name'), truck_number=request.POST.get('truck_number'), status='available'); d.save(); return redirect('manage_fleet')
    return render(request, 'manage_fleet.html', {'drivers': drivers})

@login_required
def add_load(request):
    c = request.user.userprofile.company
    if not c.is_active: return render(request, 'payment_pending.html')
    if request.method == 'POST':
        form = LoadForm(c, request.POST, request.FILES)
        if form.is_valid(): l = form.save(commit=False); l.company = c; l.save(); return redirect('manage_loads')
    return render(request, 'add_load.html', {'form': LoadForm(c)})

@login_required
def edit_load(request, load_id):
    l = get_object_or_404(Load, id=load_id, company=request.user.userprofile.company)
    form = LoadForm(l.company, request.POST or None, request.FILES or None, instance=l)
    if form.is_valid(): form.save(); return redirect('manage_loads')
    return render(request, 'edit_load.html', {'form': form})

@login_required
def complete_load(request, load_id):
    l = get_object_or_404(Load, id=load_id, company=request.user.userprofile.company); l.status='delivered'; l.save(); return redirect('manage_loads')

@login_required
def generate_invoice(request, load_id):
    l = get_object_or_404(Load, id=load_id, company=request.user.userprofile.company); return render(request, 'invoice.html', {'load': l, 'company': l.company})

@login_required
def company_settings(request):
    c = request.user.userprofile.company; form = CompanyDocForm(request.POST or None, instance=c)
    if form.is_valid(): form.save(); return redirect('dashboard')
    return render(request, 'company_settings.html', {'form': form})

@login_required
def document_center(request):
    c = request.user.userprofile.company
    if not c.is_active: return render(request, 'payment_pending.html')
    return render(request, 'document_center.html', {'company': c, 'drivers': Driver.objects.filter(company=c), 'loads': Load.objects.filter(company=c)})

@login_required
def manage_clients(request):
    c = request.user.userprofile.company; return render(request, 'manage_clients.html', {'owners': UserProfile.objects.filter(company=c, role='owner')})

@login_required
def client_dashboard(request): return render(request, 'client_dashboard.html')

# --- PUBLIC STATIC ---
def home(request): return render(request, 'home.html')
def portal_choice(request): return render(request, 'portal_choice.html')
def public_plans(request): return render(request, 'public_plans.html')
def contact_us(request): return render(request, 'contact_us.html')
def refund_policy(request): return render(request, 'refund_policy.html')
def custom_logout(request): logout(request); return redirect('home')