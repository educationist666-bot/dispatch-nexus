from django import forms
from django.contrib.auth.models import User
from .models import Load, Driver, Company

# 1. FULL REGISTRATION FORM
class RegistrationForm(forms.ModelForm):
    company_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    dot_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DOT Number'}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    address = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street Address'}))
    city = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    state = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}))
    zip_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip Code'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

# 2. DRIVER / FLEET FORM
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = '__all__'
        exclude = ['company']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# 3. LOAD FORM
class LoadForm(forms.ModelForm):
    class Meta:
        model = Load
        fields = [
            'broker_name', 'broker_mc', 'load_ref', 'rate_confirmation', 'bill_of_lading',
            'origin', 'destination', 'pickup_date', 'delivery_date', 
            'rate', 'miles', 'driver_pay', 'driver'
        ]
    def __init__(self, user_company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        if user_company:
            self.fields['driver'].queryset = Driver.objects.filter(company=user_company)
        self.fields['pickup_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        self.fields['delivery_date'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})

# 4. ONBOARDING DOCUMENTS
class OnboardingDocForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['authority_doc', 'authority_expiry', 'w9_doc', 'insurance_doc', 'insurance_expiry']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'expiry' in field:
                self.fields[field].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

# 5. PAYMENT RECEIPT FORM
class PaymentReceiptForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['payment_receipt']
        widgets = {'payment_receipt': forms.ClearableFileInput(attrs={'class': 'form-control'})}

# 6. COMPANY SETTINGS FORM (This was missing!)
class CompanyDocForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'logo', 'address', 'city', 'state', 'zip_code', 'phone', 
            'authority_doc', 'w9_doc', 'insurance_doc'
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

# 7. CLIENT/OWNER USER FORM
class ClientUserForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))