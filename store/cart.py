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
            self.cart[book_id] = {'quantity': 1, 'price': str(book.price)}
        else:
            if self.cart[book_id]['quantity'] < 10:
                self.cart[book_id]['quantity'] += 1
        self.save()


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
        book_map = {str(book.id): book for book in books}

        for book_id, item in self.cart.items():
            item_copy = item.copy()
            item_copy['book'] = book_map.get(book_id)
            item_copy['price'] = Decimal(item_copy['price'])
            item_copy['total_price'] = item_copy['price'] * item_copy['quantity']
            yield item_copy


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(item['total_price'] for item in self)

    
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
        
