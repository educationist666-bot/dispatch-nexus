from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- 1. COMPANY (The Tenant) ---
class Company(models.Model):
    # The owner who registered the company
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owned_company')
    name = models.CharField(max_length=100, default="New Logistics Co")
    
    # Subscription & Approval Logic
    plan_type = models.CharField(max_length=20, choices=[
        ('starter', 'Starter ($0)'),
        ('pro', 'Pro ($50)'),
        ('enterprise', 'Enterprise ($100)')
    ], default='starter')
    is_approved = models.BooleanField(default=False) # HQ must approve this
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# --- 2. USER PROFILE (Staff/Employees) ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # Link user to a specific company so they only see THAT company's data
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    
    role = models.CharField(max_length=20, choices=[
        ('hq_admin', 'HQ Admin'), # Superuser/Approver
        ('dispatcher', 'Dispatcher'),
        ('owner', 'Truck Owner'),
        ('driver', 'Driver')
    ], default='dispatcher')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

# --- 3. ASSETS (Isolated by Company) ---
# All models below have a 'company' field. 
# This guarantees Company A never sees Company B's trucks.

class Driver(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE) # Data Isolation
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, default='Active')
    
    def __str__(self):
        return self.name

class Truck(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE) # Data Isolation
    unit_number = models.CharField(max_length=20)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=50, default='Dry Van')
    status = models.CharField(max_length=20, default='Active') 

    def __str__(self):
        return f"{self.unit_number} ({self.company.name})"

class Load(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE) # Data Isolation
    load_ref = models.CharField(max_length=50)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='booked')

    def __str__(self):
        return self.load_ref