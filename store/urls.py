from django.urls import path, register_converter
from . import views
from .converters import SignedIntConverter

register_converter(SignedIntConverter, 'signed_int')
app_name = 'store'

urlpatterns = [
	path('', views.index, name = "index"),
    path('search/', views.search, name = "search"),
    path('login', views.signin, name="signin"),
	path('logout', views.signout, name="signout"),
	path('registration', views.registration, name="registration"),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
	path('book/<int:id>', views.get_book, name="book"),
	path('books', views.get_books, name="books"),
	path('category/<str:category_name>/', views.get_book_category, name="category"),
    path('cart/', views.cart_details, name='cart_details'),
	path('summary', views.cart_summary, name='cart_summary'),
	path('totalcart', views.total_cart, name='totalcart'),
	path('add_to_cart/<int:bookid>', views.cart_add, name='cart_add'),
	path('remove_from_cart/<int:bookid>', views.cart_remove, name='cart_remove'),
	path('update_cart/<int:bookid>/<signed_int:quantity>', views.cart_update, name='cart_update'),
	path('order_create/', views.order_create, name='order_create'),
    path('order_list/', views.order_list, name='order_list'),
    path('order_details/<int:id>/', views.order_details, name='order_details'),
    path('payment/', views.payment, name='payment'),
    path('order_success/<int:order_id>/<int:payment_id>', views.order_success, name='order_success'),
	path('pdf/<int:id>/', views.get_pdf, name='get_pdf'),
    path('seller/orders/', views.handle_orders, name='handle_orders'),
    path('seller/orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('seller/books/', views.view_books, name='view_books'),
    path('seller/books/add/', views.add_book, name='add_book'),
    path('seller/books/delete/<int:book_id>/', views.delete_book, name='delete_book'),
]