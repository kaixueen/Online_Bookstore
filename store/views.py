from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views import View
from django.http import HttpResponse, Http404, JsonResponse

from .models import Book, Slider, CustomerProfile, Order
from .forms import RegistrationForm, OrderCreateForm
from .cart import Cart
from .utils import renderPdf

def index(request):
    newpublished = Book.objects.order_by('-created_at')[:4]
    bestsellers = Book.objects.order_by('items_sold')[:4]
    slide = Slider.objects.order_by('-created_at').order_by('?')[:1]
    cart = Cart(request)
    context = {
        "newbooks": newpublished,
        "bestsellers": bestsellers,
        "slide": slide,
        "cart": cart,
    }
    return render(request, 'index.html', context)


def signin(request):
    if request.user.is_authenticated:
        return redirect('store:index')
    else:
        if request.method == "POST":
            user = request.POST.get('user')
            password = request.POST.get('pass')
            auth = authenticate(request, username=user, password=password)
            if auth is not None:
                login(request, auth)
                return redirect('store:index')
            else:
                messages.error(request, 'Username and password don\'t match')

        return render(request, "login.html")


def signout(request):
    logout(request)
    return redirect('store:index') 


def registration(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('store:signin')

    return render(request, 'signup.html', {"form": form})


def payment(request):
    return render(request, 'payment.html')


def get_book(request, id):
    book = get_object_or_404(Book, id=id)
    
    rbooks = Book.objects.filter(category=book.category)

    context = {
        "book": book,
        "rbooks": rbooks,
    }
    return render(request, "book.html", context)


def get_books(request):
    books_ = Book.objects.all().order_by('-created_at')
    paginator = Paginator(books_, 10)
    page = request.GET.get('page')
    books = paginator.get_page(page)
    return render(request, "category.html", {"book": books})


def get_book_category(request, category_name):
    book_ = Book.objects.filter(category=category_name)
    paginator = Paginator(book_, 10)
    page = request.GET.get('page')
    book = paginator.get_page(page)
    return render(request, "category.html", {"book": book})


def search(request):
    search = request.GET.get('q')
    books = Book.objects.all()
    if search:
        books = books.filter(
            Q(name__icontains=search) | 
            Q(category__icontains=search) | 
            Q(writer__icontains=search)
        )

    paginator = Paginator(books, 10)
    page = request.GET.get('page')
    books = paginator.get_page(page)

    context = {
        "book": books,
        "search": search,
    }
    return render(request, 'category.html', context) 


def cart_add(request, bookid):
    cart = Cart(request)  
    book = get_object_or_404(Book, id=bookid) 
    cart.add(book=book)

    total_items = len(cart)  
    return JsonResponse({'success': True, 'total_items': total_items})


def cart_update(request, bookid, quantity):
    cart = Cart(request) 
    book = get_object_or_404(Book, id=bookid) 
    cart.update(book=book, quantity=quantity)
    price = cart.get_price(book)
    quantity = cart.get_quantity(book)

    return JsonResponse({'success': True, 'price': price, 'quantity': quantity})


def cart_remove(request, bookid):
    cart = Cart(request)
    book = get_object_or_404(Book, id=bookid)
    cart.remove(book)
    return render(request, 'cart.html', {"cart": cart})


def total_cart(request):
    cart = Cart(request)
    return render(request, 'totalcart.html', {"cart": cart})


def cart_summary(request):
    return render(request, 'summary.html')


def cart_details(request):
    cart = Cart(request)
    context = {
        "cart": cart,
    }
    return render(request, 'cart.html', context)


def order_create(request):
    cart = Cart(request)
    if not request.user.is_authenticated:
        return redirect('store:signin')

    if len(cart) == 0:
        return redirect('store:books')

    try:
        customer = CustomerProfile.objects.get(user=request.user)
    except CustomerProfile.DoesNotExist:
        customer = CustomerProfile.objects.create(user=request.user)

    form = OrderCreateForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            for item in cart:
                order = form.save(commit=False)
                order.customer = customer 
                order.book = item['book']
                order.price = item['price']
                order.quantity = item['quantity']
                order.payable = item['price'] * item['quantity']
                order.save()
            cart.clear()
            messages.success(request, "Your order has been placed successfully.")
            return render(request, 'order/successfull.html')
        else:
            messages.error(request, "Fill out your information correctly.")

    if request.method != 'POST':
        form.initial['name'] = request.user.first_name
        form.initial['email'] = request.user.email

    return render(request, 'order/order.html', {"form": form})


def order_list(request):
    if not request.user.is_authenticated:
        return redirect('store:signin')

    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        my_order = Order.objects.filter(customer=customer_profile).order_by('-created')
        paginator = Paginator(my_order, 5)
        page = request.GET.get('page')
        myorder = paginator.get_page(page)
        
        return render(request, 'order/list.html', {"myorder": myorder})
    except CustomerProfile.DoesNotExist:
        messages.error(request, "You don't have a customer profile yet.")
        return redirect('store:index')


def order_details(request, id):
    if not request.user.is_authenticated:
        return redirect('store:signin')

    order_summary = get_object_or_404(Order, id=id)

    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        if order_summary.customer != customer_profile:
            return redirect('store:index')
    except CustomerProfile.DoesNotExist:
        return redirect('store:index')

    context = {
        "order": order_summary
    }
    return render(request, 'order/details.html', context)


class pdf(View):  
    def get(self, request, id):
        try:
            query = get_object_or_404(Order, id=id)
            
            try:
                customer_profile = CustomerProfile.objects.get(user=request.user)
                if query.customer != customer_profile:
                    raise Http404('Content not found')
            except CustomerProfile.DoesNotExist:
                raise Http404('Content not found')
                
        except Http404:
            raise Http404('Content not found')
        
        context = {
            "order": query
        }
        article_pdf = renderPdf('order/pdf.html', context)
        return HttpResponse(article_pdf, content_type='application/pdf')