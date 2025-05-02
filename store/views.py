from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views import View
from django.http import HttpResponse, Http404, JsonResponse
from decimal import Decimal
from .models import Book, Slider, CustomerProfile, Order, Payment
from .forms import RegistrationForm, OrderCreateForm
from .cart import Cart
from .utils import renderPdf
import uuid

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

@login_required
def signout(request):
    logout(request)
    return redirect('store:index') 


def registration(request):
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('store:signin')

    return render(request, 'signup.html', {"form": form})


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
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    cart = Cart(request)
    book = get_object_or_404(Book, id=bookid)
    cart.add(book=book)

    total_items = len(cart)
    return JsonResponse({'success': True, 'total_items': total_items})

@login_required(login_url='store:signin')
def cart_update(request, bookid, quantity):
    cart = Cart(request) 
    book = get_object_or_404(Book, id=bookid) 
    cart.update(book=book, quantity=quantity)
    price = cart.get_price(book)
    quantity = cart.get_quantity(book)

    return JsonResponse({'success': True, 'price': price, 'quantity': quantity})

@login_required(login_url='store:signin')
def cart_remove(request, bookid):
    cart = Cart(request)
    book = get_object_or_404(Book, id=bookid)
    cart.remove(book)
    return render(request, 'cart.html', {"cart": cart})

@login_required(login_url='store:signin')
def total_cart(request):
    cart = Cart(request)
    return render(request, 'totalcart.html', {"cart": cart})

@login_required(login_url='store:signin')
def cart_summary(request):
    return render(request, 'summary.html')

@login_required(login_url='store:signin')
def cart_details(request):
    cart = Cart(request)
    context = {
        "cart": cart,
    }
    return render(request, 'cart.html', context)


@login_required(login_url='store:signin')
def order_create(request):
    cart = request.session.get('cart', {})
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if not cart:
        return redirect('store:cart')  

    cart_items = []
    total_price = 0

    for book_id, item in cart.items():
        book = get_object_or_404(Book, id=book_id)
        quantity = item.get('quantity', 1)
        price = Decimal(item.get('price', book.price))
        subtotal = price * quantity
        total_price += subtotal
        cart_items.append({'book': book, 'quantity': quantity, 'price': price, 'subtotal': subtotal})

    if request.method == 'POST':
        order = Order.objects.create(customer=customer_profile, books=cart)
        request.session['order_id'] = order.id
        request.session.pop('cart', None) 
        return redirect('store:payment') 

    return render(request, 'order_create.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'customer_profile': customer_profile,
    })

@login_required(login_url='store:signin')
def payment(request):
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, "No order found. Please try again.")
        return redirect('store:order_create')

    order = get_object_or_404(Order, id=order_id)
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        account_no = request.POST.get('account_no', '')
        amount_paid = Decimal(request.POST.get('amount_paid', '0'))

        if payment_method == 'cash_on_delivery':
            order.paid = False
            order.save()
            return redirect('store:order_success', order_id=order_id, payment_id=0)

        transaction_id = str(uuid.uuid4())

        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            account_no=account_no,
            transaction_id=transaction_id,
            amount_paid=amount_paid
        )

        order.paid = True
        order.save()
        request.session.pop('order_id', None) 
        return redirect('store:order_success', order_id=order_id, payment_id=payment.id)

    return render(request, 'payment.html', {
        'order': order,
        'customer_profile': customer_profile
    })

@login_required(login_url='store:signin')
def order_success(request, order_id, payment_id):
    order = get_object_or_404(Order, id=order_id)
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)
    books = []
    for id, details in order.books.items():
        book = get_object_or_404(Book, id=id)
        books.append({'name': book.name, 'quantity': details['quantity']})

    if order.customer != customer_profile:
        return redirect('store:index')

    payment = None
    if payment_id and int(payment_id) != 0:
        try:
            payment = Payment.objects.get(id=payment_id, order=order)
        except Payment.DoesNotExist:
            pass

    return render(request, 'order_success.html', {
        'order': order,
        'books': books,
        'payment': payment
    })


@login_required(login_url='store:signin')
def order_list(request):
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)
    orders = Order.objects.filter(customer=customer_profile).order_by('-created')

    order_list = []
    for order in orders:
        quantity = sum(details['quantity'] for details in order.books.values())
        order_list.append({'order': order, 'quantity': quantity})

    paginator = Paginator(order_list, 5) 
    page_number = request.GET.get('page')
    paginated_order_list = paginator.get_page(page_number)

    return render(request, 'order_list.html', {'orders': paginated_order_list})

@login_required(login_url='store:signin')
def order_details(request, id):
    order = get_object_or_404(Order, id=id)
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if order.customer != customer_profile:
        return redirect('store:index')
    
    books = []
    for id, details in order.books.items():
        book = get_object_or_404(Book, id=id)
        details['subtotal'] = Decimal(book.price) * details['quantity']  
        books.append((book, details))

    if order.paid:
        payment = Payment.objects.filter(order=order).first()
    else:
        payment = None
    total_price = order.get_cost()

    return render(request, 'order_details.html', {
        'order': order,
        'books': books,
        'payment': payment,
        'total_price': total_price,
    })


class pdf(View):
    @login_required(login_url='store:signin')
    def get(self, request, id):
        order = get_object_or_404(Order, id=id)

        try:
            customer_profile = CustomerProfile.objects.get(user=request.user)
            if order.customer != customer_profile:
                raise Http404("Content not found")
        except CustomerProfile.DoesNotExist:
            raise Http404("Content not found")

        books = []
        for id, details in order.books.items():
            book = get_object_or_404(Book, id=id)
            books.append((book.name, details['quantity'], book.price, details['quantity'] * book.price))

        context = {"order": order, "books": books}
        article_pdf = renderPdf('pdf.html', context)

        response = HttpResponse(article_pdf, content_type='application/pdf')
        filename = f"Order_Receipt_{order.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response