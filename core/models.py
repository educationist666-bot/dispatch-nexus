from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

class Company(models.Model):
    PLAN_CHOICES = (('starter', 'Starter'), ('pro', 'Professional'), ('enterprise', 'Enterprise'))
    name = models.CharField(max_length=200)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_owned')
    dot_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    payment_receipt = models.ImageField(upload_to='payment_receipts/', blank=True, null=True)
    payment_submitted_at = models.DateTimeField(null=True, blank=True)
    
    authority_doc = models.FileField(upload_to='company_docs/', blank=True, null=True)
    authority_expiry = models.DateField(null=True, blank=True)
    insurance_doc = models.FileField(upload_to='company_docs/', blank=True, null=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    w9_doc = models.FileField(upload_to='company_docs/', blank=True, null=True)

    def __str__(self): return self.name
    
    @property
    def has_access(self):
        if not self.is_active or not self.subscription_end_date: return False
        return self.subscription_end_date > timezone.now()

    @property
    def days_remaining(self):
        if not self.subscription_end_date: return 0
        delta = self.subscription_end_date - timezone.now()
        return max(0, delta.days)

class UserProfile(models.Model):
    ROLE_CHOICES = (('admin', 'Dispatcher'), ('client', 'Truck Owner'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    def __str__(self): return self.user.username

class Driver(models.Model):
    TRUCK_TYPES = (('dry_van', "Dry Van (53')"), ('reefer', 'Reefer'), ('flatbed', 'Flatbed'), ('power_only', 'Power Only'), ('box_truck', 'Box Truck'))
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    truck_number = models.CharField(max_length=20)
    truck_type = models.CharField(max_length=20, choices=TRUCK_TYPES, default='dry_van')
    status = models.CharField(max_length=20, default='ready')
    cdl = models.FileField(upload_to='fleet_docs/', blank=True, null=True)
    medical_card = models.FileField(upload_to='fleet_docs/', blank=True, null=True)
    registration = models.FileField(upload_to='fleet_docs/', blank=True, null=True)
    def __str__(self): return f"{self.truck_number} - {self.name}"

class Load(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Restored Missing Fields
    broker_name = models.CharField(max_length=200, default="TBD")
    broker_mc = models.CharField(max_length=20, default="000000")
    load_ref = models.CharField(max_length=50)
    rate_confirmation = models.FileField(upload_to='load_docs/', blank=True, null=True)
    bill_of_lading = models.FileField(upload_to='load_docs/', blank=True, null=True)
    
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    pickup_date = models.DateTimeField()
    delivery_date = models.DateTimeField()
    
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    miles = models.IntegerField(default=0) # Restored
    driver_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, default='booked')

    def save(self, *args, **kwargs):
        self.net_profit = self.rate - (self.driver_pay or 0)
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: UserProfile.objects.create(user=instance)