from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# --- 1. COMPANY ---
class Company(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_company')
    name = models.CharField(max_length=100)
    dot_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    # Compliance
    mc_cert = models.FileField(upload_to='compliance/mc/', blank=True, null=True)
    mc_expiry = models.DateField(null=True, blank=True)
    insurance_cert = models.FileField(upload_to='compliance/ins/', blank=True, null=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    w9_cert = models.FileField(upload_to='compliance/w9/', blank=True, null=True)

    # SaaS
    plan_type = models.CharField(max_length=20, choices=[('starter', 'Starter'), ('pro', 'Pro'), ('enterprise', 'Enterprise')], default='starter')
    is_active = models.BooleanField(default=False)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    payment_receipt = models.ImageField(upload_to='receipts/', blank=True, null=True)
    payment_submitted_at = models.DateTimeField(null=True, blank=True)

    @property
    def days_remaining(self):
        if self.subscription_end_date and self.is_active:
            delta = self.subscription_end_date - timezone.now()
            return max(0, delta.days)
        return 0

    @property
    def has_access(self):
        if not self.is_active: return False
        if self.subscription_end_date and self.subscription_end_date < timezone.now(): return False
        return True

    def __str__(self): return self.name

# --- 2. USER PROFILE ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, default='dispatcher') 

# --- 3. FLEET ASSETS ---
class Driver(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    
    # Driver Docs
    cdl_file = models.FileField(upload_to='drivers/cdl/', blank=True, null=True)
    medical_card_file = models.FileField(upload_to='drivers/medical/', blank=True, null=True)
    driver_w9_file = models.FileField(upload_to='drivers/w9/', blank=True, null=True)

    # Truck Info
    truck_number = models.CharField(max_length=50)
    truck_type = models.CharField(max_length=50, choices=[('Dry Van', 'Dry Van'), ('Reefer', 'Reefer'), ('Flatbed', 'Flatbed')], default='Dry Van')
    status = models.CharField(max_length=20, default='Active')

    # Truck Docs
    registration_file = models.FileField(upload_to='trucks/registration/', blank=True, null=True)
    insurance_file = models.FileField(upload_to='trucks/insurance/', blank=True, null=True)
    ifta_sticker_file = models.FileField(upload_to='trucks/ifta/', blank=True, null=True)
    
    def __str__(self): return self.name

# --- 4. LOADS (Fixed with Broker Details) ---
class Load(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Broker Info (NEW)
    broker_name = models.CharField(max_length=100, default="")
    broker_mc = models.CharField(max_length=50, default="")
    
    load_ref = models.CharField(max_length=50)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    
    pickup_date = models.DateTimeField(default=timezone.now)
    delivery_date = models.DateTimeField(default=timezone.now)
    
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    miles = models.IntegerField(default=0) # (NEW)
    expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, default='booked', choices=[
        ('booked', 'Booked'), ('active', 'In Transit'), ('delivered', 'Delivered'), ('paid', 'Paid')
    ])
    
    # Docs
    rate_con_file = models.FileField(upload_to='loads/ratecons/', blank=True, null=True)
    bol_file = models.FileField(upload_to='loads/bol/', blank=True, null=True)
    pod_file = models.FileField(upload_to='loads/pod/', blank=True, null=True)

    @property
    def net_profit(self):
        return self.rate - self.expenses