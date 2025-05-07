from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Order, CustomerProfile, Book

class RegistrationForm(UserCreationForm):
    name = forms.CharField(required=True, max_length=150, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone_number = forms.CharField(required=False, max_length=15, label="Phone Number")
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label="Address")

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']  

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            CustomerProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                address=self.cleaned_data.get('address', '')
            )
        return user
    
class OrderCreateForm(forms.ModelForm):
    PAYMENT_METHOD_CHOICES = (
        ('TNG E-wallet', 'TNG E-wallet'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash on Delivery', 'Cash on Delivery'),
    )

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-method'}),
        required=True
    )
    account_no = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Account No'}),
    )
    transaction_id = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Transaction ID'}),
    )

    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'quantity-input'}),
        required=True
    )

    class Meta:
        model = Order
        fields = ['payment_method', 'account_no', 'transaction_id', 'quantity']

    def clean_account_no(self):
        account_no = self.cleaned_data.get('account_no')
        if not account_no.isdigit():
            raise forms.ValidationError("Account number must contain only digits.")
        return account_no

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get('transaction_id')
        if len(transaction_id.strip()) < 5:
            raise forms.ValidationError("Transaction ID must be at least 5 characters long.")
        return transaction_id

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['name', 'writer', 'category', 'price', 'items_sold', 'description', 'coverpage', 'status']