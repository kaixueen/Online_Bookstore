from django.contrib import admin

# Register your models here.
from .models import Book, Slider, CustomerProfile, Order, Payment, SellerProfile, LoginActivityLog, PaymentLog

admin.site.register(Book)
admin.site.register(Slider)
admin.site.register(CustomerProfile)
admin.site.register(SellerProfile)
admin.site.register(Order)
admin.site.register(Payment)
admin.site.register(PaymentLog)
admin.site.register(LoginActivityLog)

