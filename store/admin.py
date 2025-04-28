from django.contrib import admin

# Register your models here.
from .models import Book, Slider, CustomerProfile, Order, Payment

admin.site.register(Book)
admin.site.register(Slider)
admin.site.register(CustomerProfile)
admin.site.register(Order)
admin.site.register(Payment)
