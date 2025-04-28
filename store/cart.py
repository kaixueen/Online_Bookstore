from decimal import Decimal
from django.conf import settings
from .models import Book


class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, book):
        book_id = str(book.id)
        if book_id not in self.cart:
            self.cart[book_id] = {'quantity': 0, 'price': str(book.price)}
            self.cart[book_id]['quantity'] = 1
        else:    
            if self.cart[book_id]['quantity'] < 10:
                self.cart[book_id]['quantity'] += 1
        print(f"Cart after adding {book.id}: {self.cart}")
        self.save()
        print(f"Cart after adding {book.id}: {self.cart}")

    def update(self, book, quantity):
        book_id = str(book.id)
        self.cart[book_id]['quantity'] += quantity

        if self.cart[book_id]['quantity'] <= 0:
            self.cart[book_id]['quantity'] = 0
            del self.cart[book_id]
        
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True
        print(f"Session saved: {self.session.get(settings.CART_SESSION_ID)}")

    def remove(self, book):
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def __iter__(self):
        book_ids = self.cart.keys()
        books = Book.objects.filter(id__in=book_ids)
        for book in books:
            self.cart[str(book.id)]['book'] = book

        for item in self.cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
    
    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_price(self, book):
        book_id = str(book.id)
        if book_id in self.cart:
            return Decimal(self.cart[book_id]['price']) * self.cart[book_id]['quantity']
        return Decimal(0)

    def get_quantity(self, book):
        book_id = str(book.id)
        if book_id in self.cart:
            return self.cart[book_id]['quantity']
        return 0

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True
        
