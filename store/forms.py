from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
import re
from .models import Order, CustomerProfile, Book

class RegistrationForm(UserCreationForm):
    name = forms.CharField(
        required=True,
        max_length=150,
        label="Full Name",
        validators=[
            RegexValidator(r'^[a-zA-Z\s.\'-]+$', 'Name contains invalid characters.')
        ]
    )
    email = forms.EmailField(required=True, label="Email Address")
    
    phone_number = forms.CharField(
        required=False,
        max_length=15,
        label="Phone Number",
        validators=[
            RegexValidator(r'^\+?\d{7,15}$', 'Enter a valid phone number.')
        ]
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        max_length=300,
        label="Address"
    )

    consent = forms.BooleanField(
        required=True,
        label="I agree to the Privacy Policy and data usage terms.",
        error_messages={
            'required': 'You must agree to the privacy policy to register.'
        }
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'consent']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email.strip().lower()

    def clean_address(self):
        address = self.cleaned_data.get('address', '').strip()
        if len(address) > 300:
            raise forms.ValidationError("Address is too long.")
        return address

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['name'].strip()
        user.email = self.cleaned_data['email'].strip().lower()

        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', '').strip(),
                address=self.cleaned_data.get('address', '').strip()
            )
        return user

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['name', 'writer', 'category', 'price', 'items_sold', 'description', 'coverpage', 'status']