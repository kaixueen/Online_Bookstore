from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class Book(models.Model):
    name = models.CharField(max_length=100)
    writer = models.CharField(max_length=100) 
    category = models.CharField(max_length=100) 
    price = models.IntegerField()
    items_sold = models.IntegerField()
    description = models.TextField()
    coverpage = models.FileField(upload_to="coverpage/")
    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Slider(models.Model):
    title = models.CharField(max_length=150)
    slide_img = models.FileField(upload_to="slide/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Order(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'Order {self.id} - {self.book.name}'

    def get_cost(self):
        return self.book.price * self.quantity

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20)
    account_no = models.CharField(max_length=20)
    transaction_id = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment {self.transaction_id}'