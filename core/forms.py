from django import forms
from .models import Load, Driver, Company

# --- 1. REGISTRATION ---
class RegistrationForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@company.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Secure Password'}))
    company_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    dot_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USDOT #', 'id': 'dot-mask'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 000-0000', 'id': 'phone-mask'}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}))
    zip_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zip'}))

# --- 2. COMPLIANCE ---
class OnboardingDocForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['mc_cert', 'mc_expiry', 'insurance_cert', 'insurance_expiry', 'w9_cert']
        widgets = {
            'mc_cert': forms.FileInput(attrs={'class': 'form-control'}),
            'mc_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'insurance_cert': forms.FileInput(attrs={'class': 'form-control'}),
            'insurance_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'w9_cert': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PaymentReceiptForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['payment_receipt']
        widgets = {'payment_receipt': forms.FileInput(attrs={'class': 'form-control'})}

class CompanyDocForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'phone', 'address', 'city', 'state', 'zip_code']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields: self.fields[field].widget.attrs.update({'class': 'form-control'})

# --- 3. DRIVER FORM ---
class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            'name', 'phone', 'truck_number', 'truck_type', 'status',
            'cdl_file', 'medical_card_file', 'driver_w9_file',
            'registration_file', 'insurance_file', 'ifta_sticker_file'
        ]
        widgets = {
            'cdl_file': forms.FileInput(attrs={'class': 'form-control'}),
            'medical_card_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
             if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

# --- 4. LOAD FORM (The Fix) ---
class LoadForm(forms.ModelForm):
    # Explicitly define optional fields so they don't crash the form if empty
    broker_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    broker_mc = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    miles = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    expenses = forms.DecimalField(required=False, initial=0.00, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    
    # Force Rate Con to be a File Input
    rate_con_file = forms.FileField(required=True, widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}))

    class Meta:
        model = Load
        fields = [
            'broker_name', 'broker_mc', 'load_ref', 
            'rate_con_file', 
            'origin', 'destination', 'pickup_date', 'delivery_date', 
            'driver', 'rate', 'miles', 'expenses', 'status'
        ]
        widgets = {
            'pickup_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'delivery_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, company, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = Driver.objects.filter(company=company)
        for field in self.fields:
             if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})