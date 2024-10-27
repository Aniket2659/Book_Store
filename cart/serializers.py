from rest_framework import serializers
from .models import CartModel, CartItems
from book.models import Book

class CartItemsSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(slug_field='name', queryset=Book.objects.all())

    class Meta:
        model=CartItems
        fields=['id','book','quantity','price']

class CartSerializer(serializers.ModelSerializer):
    items=CartItemsSerializer(many=True, read_only=True)

    class Meta:
        model=CartModel
        fields=['id','total_price',"total_quantity","is_ordered",'user','items']
