from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# --- 1. USER PROFILE ---
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, default='dispatcher')  
    plan_type = models.CharField(max_length=20, default='starter')

    def __str__(self):
        return self.user.username

# --- 2. COMPANY SETTINGS ---
class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="My Logistics Co")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    subscription_status = models.CharField(max_length=20, default='active')
    days_remaining = models.IntegerField(default=14)

    def __str__(self):
        return self.name

# --- 3. DRIVER MODEL ---
class Driver(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default='Active')
    
    def __str__(self):
        return self.name

# --- 4. TRUCK MODEL ---
class Truck(models.Model):
    unit_number = models.CharField(max_length=20)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=50, choices=[
        ('Dry Van', 'Dry Van'), 
        ('Reefer', 'Reefer'), 
        ('Flatbed', 'Flatbed')
    ], default='Dry Van')
    status = models.CharField(max_length=20, default='Active') 

    def __str__(self):
        return f"Unit {self.unit_number}"

# --- 5. LOAD MODEL ---
class Load(models.Model):
    load_ref = models.CharField(max_length=50, verbose_name="Load Reference")
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    pickup_date = models.DateField(default=timezone.now) 
    
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=[
        ('booked', 'Booked'),
        ('active', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='booked')

    @property
    def net_profit(self):
        return self.rate - self.expenses

    def __str__(self):
        return f"{self.load_ref}: {self.origin} -> {self.destination}"