from django.db import models
from django.conf import settings
from book.models import Book

class CartModel(models.Model):
    total_price=models.PositiveBigIntegerField(default=0)
    total_quantity=models.PositiveBigIntegerField(default=0)
    is_ordered=models.BooleanField(default=False)
    user= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')

    class Meta:
        db_table="cart"

class CartItems(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='cart_items')
    cart = models.ForeignKey(CartModel, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=0) 

    class Meta:
        db_table = 'cart_item'
