from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.views import View
from django.http import HttpResponse, Http404, JsonResponse
from decimal import Decimal
from django.utils.html import escape
from .models import Book, Slider, CustomerProfile, Order, Payment, PaymentLog, User, LoginActivityLog
from .forms import RegistrationForm, BookForm
from django.utils import timezone
from django.utils.timezone import timedelta
from .cart import Cart
from .utils import renderPdf
import uuid

def is_seller(user):
    return hasattr(user, 'sellerprofile')

def is_customer(user):
    return hasattr(user, 'customerprofile')

def index(request):
    newpublished = Book.objects.order_by('-created_at')[:4]
    bestsellers = Book.objects.order_by('-items_sold')[:4]
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

    if request.method == "POST":
        username = request.POST.get('user', '').strip()
        password = request.POST.get('pass', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('store:signin')

        # Check if user exists
        user = User.objects.filter(username=username).first()
        if user:
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            recent_failed_attempts = LoginActivityLog.objects.filter(
                user=user,
                success=False,
                timestamp__gte=five_minutes_ago
            ).count()

            if recent_failed_attempts >= 3:
                messages.error(request, 'Account locked due to too many failed login attempts. Try again in 5 minutes.')
                return redirect('store:signin')

        # Authenticate will trigger `user_logged_in` or `user_login_failed` signal
        user_auth = authenticate(request, username=username, password=password)
        if user_auth:
            login(request, user_auth)
            return redirect('store:index')
        else:
            messages.error(request, 'Username and password don\'t match.')

    return render(request, "login.html")


@login_required
def signout(request):
    logout(request)
    return redirect('store:index') 


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('store:signin')
    else:
        form = RegistrationForm()
        
    return render(request, 'signup.html', {"form": form})

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

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
    query = request.GET.get('q', '').strip()
    books = Book.objects.all()
    if query:
        query = escape(query) 
        books = books.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(writer__icontains=query)
        )

    paginator = Paginator(books, 10)
    page = request.GET.get('page')
    books = paginator.get_page(page)

    context = {
        "book": books,
        "search": query,
    }
    return render(request, 'category.html', context)


@user_passes_test(is_customer)
def cart_add(request, bookid):
    if not request.user.is_authenticated:
        return JsonResponse({'login_required': True}, status=401)

    cart = Cart(request)
    book = get_object_or_404(Book, id=bookid)
    cart.add(book=book)

    total_items = len(cart)
    return JsonResponse({'success': True, 'total_items': total_items})

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def cart_update(request, bookid, quantity):
    cart = Cart(request) 
    book = get_object_or_404(Book, id=bookid) 
    cart.update(book=book, quantity=quantity)
    price = cart.get_price(book)
    quantity = cart.get_quantity(book)

    return JsonResponse({'success': True, 'price': price, 'quantity': quantity})


@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def cart_remove(request, bookid):
    cart = Cart(request)
    book = get_object_or_404(Book, id=bookid)
    cart.remove(book)
    return render(request, 'cart.html', {"cart": cart})

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def total_cart(request):
    cart = Cart(request)
    return render(request, 'totalcart.html', {"cart": cart})

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def cart_summary(request):
    return render(request, 'summary.html')

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def cart_details(request):
    cart = Cart(request)
    context = {
        "cart": cart,
    }
    return render(request, 'cart.html', context)

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def order_create(request):
    cart = request.session.get('cart', {})

    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if not cart:
        return redirect('store:cart')

    cart_items = []
    total_price = 0

    for book_id, item in cart.items():
        try:
            book_id = int(book_id)
            book = get_object_or_404(Book, id=book_id)
        except (ValueError, Book.DoesNotExist):
            continue

        quantity = int(item.get('quantity', 1))
        quantity = max(1, quantity)
        price = Decimal(item.get('price', book.price))
        subtotal = price * quantity
        total_price += subtotal
        cart_items.append({'book': book, 'quantity': quantity, 'price': price, 'subtotal': subtotal})

    if request.method == 'POST':
        try:
            order = Order.objects.create(customer=customer_profile, books=cart)
        except Exception as e:
            messages.error(request, "Unable to create order.")
            return redirect('store:cart')

        request.session['order_id'] = order.id
        request.session.pop('cart', None)
        return redirect('store:payment')

    return render(request, 'order_create.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'customer_profile': customer_profile,
    })


@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def payment(request):
    order_id = request.session.get('order_id')

    if not order_id:
        messages.error(request, "No order found. Please try again.")
        return redirect('store:order_create')

    try:
        order_id = int(order_id)
        order = get_object_or_404(Order, id=order_id)
    except (ValueError, Order.DoesNotExist) as e:
        messages.error(request, "Invalid order.")
        return redirect('store:order_create')

    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if request.method == 'POST':

        payment_method = request.POST.get('payment_method', '').strip()
        account_no = request.POST.get('account_no', '').strip()
        amount_paid = order.get_cost()

        try:
            amount_paid = Decimal(amount_paid)
            if amount_paid <= 0:
                raise ValueError("Amount is zero or negative.")
        except Exception as e:
            messages.error(request, "Invalid amount.")
            return redirect('store:payment')

        transaction_id = str(uuid.uuid4())

        try:
            payment = Payment.objects.create(
                order=order,
                customer=customer_profile,
                payment_method=payment_method,
                account_no=account_no if payment_method != 'cash_on_delivery' else '',
                transaction_id=transaction_id,
                amount_paid=amount_paid
            )

            PaymentLog.objects.create(
                customer=customer_profile,
                payment_method=payment_method,
                transaction_id=transaction_id,
                amount=amount_paid,
                status='Success',
            )

            order.paid = (payment_method != 'cash_on_delivery')
            order.save()

            request.session.pop('order_id', None)

            return redirect('store:order_success', order_id=order_id, payment_id=payment.id)

        except Exception as e:
            messages.error(request, "Payment failed. Try again.")
            return redirect('store:payment')

    return render(request, 'payment.html', {
        'order': order,
        'customer_profile': customer_profile
    })

@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def order_success(request, order_id, payment_id):
    order = get_object_or_404(Order, id=order_id)
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    if order.customer != customer_profile:
        return redirect('store:index')

    books = []
    for id, details in order.books.items():
        book = get_object_or_404(Book, id=id)

        quantity = details['quantity']
        book.items_sold += quantity
        book.save()

        books.append({'name': book.name, 'quantity': quantity})

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
@user_passes_test(is_customer)
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
@user_passes_test(is_customer)
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


@login_required(login_url='store:signin')
@user_passes_test(is_customer)
def get_pdf(request, id):
    order = get_object_or_404(Order, id=id)

    try:
        customer_profile = CustomerProfile.objects.get(user=request.user)
        if order.customer != customer_profile:
            raise Http404("Content not found")
    except CustomerProfile.DoesNotExist:
        raise Http404("Content not found")

    books = []
    for book_id, details in order.books.items():
        book = get_object_or_404(Book, id=book_id)
        books.append((book.name, details['quantity'], book.price, details['quantity'] * book.price))

    context = {"order": order, "books": books}
    article_pdf = renderPdf('pdf.html', context)

    response = HttpResponse(article_pdf, content_type='application/pdf')
    filename = f"Order_Receipt_{order.id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url='store:signin')
@user_passes_test(is_seller)
def handle_orders(request):
    orders = Order.objects.all().select_related('customer')
    payments = Payment.objects.all()
    return render(request, 'handle_orders.html', {'orders': orders, 'payments': payments})

@login_required(login_url='store:signin')
@user_passes_test(is_seller)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.status = request.POST.get('status')
        order.paid = request.POST.get('paid') == 'True'
        order.save()
        return redirect('store:handle_orders') 

@login_required(login_url='store:signin')
@user_passes_test(is_seller)
def view_books(request):
    books = Book.objects.all()
    return render(request, 'view_books.html', {'books': books})

@login_required(login_url='store:signin')
@user_passes_test(is_seller)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('store:view_books')
    else:
        form = BookForm()
    return render(request, 'add_book.html', {'form': form})

@login_required(login_url='store:signin')
@user_passes_test(is_seller)
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    return redirect('store:view_books')
