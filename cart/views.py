from .models import CartItems,CartModel
from .serializers import CartItemsSerializer,CartSerializer
from rest_framework  import status
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from book.models import Book
from django.db import models

class CartsViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Retrieve the active cart for the authenticated user",
        operation_description="This endpoint retrieves the active (non-ordered) cart for the current authenticated user, along with the items in the cart.",
        responses={
            200: openapi.Response("Success", CartSerializer),
            404: "No active cart found for the user",
            500: "An unexpected error occurred"
        }
    )
    def get (self,request,*args, **kwargs):
        try:
            active_cart = CartModel.objects.get(user=request.user,is_ordered=False)
            if  active_cart :
                serializer = CartSerializer(active_cart)
                return Response({"message":"The active cart of the user","status":"success","data":serializer.data},status=status.HTTP_200_OK)
            
        except CartModel.DoesNotExist:
            return Response(
                {
                    "message": "No active cart found for the user",
                    "status": "error"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
                return Response(
                {
                    "message": "An unexpected error occurred",
                    "status": "error",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @swagger_auto_schema(
        operation_summary="Add or update items in the cart",
        operation_description="This endpoint adds new items to the active cart or updates the quantity of an existing item in the cart. If no active cart exists, a new cart is created.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'book_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the book to add'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity of the book to add')
            },
            required=['book_id', 'quantity']
        ),
        responses={
            200: openapi.Response("Cart updated successfully", CartSerializer),
            201: openapi.Response("New cart created successfully", CartSerializer),
            400: "book_id and quantity are required",
            500: "An error occurred while creating the cart"
        }
    )
    def post(self, request ,*args, **kwargs):
        try:  
            book_id = request.data.get('book_id')
            quantity = request.data.get('quantity')
            
            if not book_id or not quantity:
                return Response({"message": "book_id and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)
            
            book = Book.objects.get(id=book_id)
            if not book:
                return Response({"message": "Book does not exist in the database."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check book stock
            if book.stock < quantity:
                return Response({"message": f"Insufficient stock. Only {book.stock} available."}, status=status.HTTP_400_BAD_REQUEST)
                
            active_cart = CartModel.objects.filter(user=request.user, is_ordered=False).first()
            serializer = CartSerializer(active_cart)
            if active_cart:
                cart_items, items_create = CartItems.objects.get_or_create(cart=active_cart,book=book)
                if items_create:
                    cart_items.quantity = quantity
                    cart_items.price = book.price * quantity
                    cart_items.save()
                else:
                    # If the item is already in the cart, update the quantity and price
                    new_quantity = cart_items.quantity + quantity
                    if book.stock < new_quantity:
                        return Response({"message": f"Insufficient stock. Only {book.stock} available."}, status=status.HTTP_400_BAD_REQUEST)
                    cart_items.quantity = new_quantity
                    cart_items.price = book.price * new_quantity
                    cart_items.save()
                # Update the cart's total price and quantity
                active_cart.total_quantity = CartItems.objects.filter(cart=active_cart).aggregate(total=models.Sum('quantity'))['total'] or 0
                active_cart.total_price = CartItems.objects.filter(cart=active_cart).aggregate(total=models.Sum('price'))['total'] or 0
                active_cart.save()
                
                return Response(
                    {
                        "message": "The user already has an active cart",
                        "status": "success",
                        "data": serializer.data  
                    },
                    status=status.HTTP_200_OK)
            
            cart = CartModel.objects.create(user=request.user)  
            CartItems.objects.create(cart=cart, book=book, quantity=quantity, price=book.price * quantity)
            # Set the cart's total price and quantity
            cart.total_quantity = quantity
            cart.total_price = book.price * quantity
            cart.save()
            
            serializer = CartSerializer(cart)  # Serialize the new cart
            
            return Response(
                {
                    "message": "New cart created successfully",
                    "status": "success",
                    "data": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
                
            
        except Exception as e:
            return Response(
                {
                    "message": "An error occurred while creating the cart",
                    "status": "error",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @swagger_auto_schema(
        operation_summary="Delete the active cart",
        operation_description="This endpoint deletes the current active (non-ordered) cart of the user.",
        responses={
            204: "Cart deleted successfully",
            404: "No active cart found",
            500: "An unexpected error occurred"
        }
    )
    def delete(self, request, pk=None, *args, **kwargs):
        try:
            # If a specific cart item id is provided, delete only that item
            if pk:
                active_cart = CartModel.objects.filter(user=request.user, is_ordered=False).first()
                if not active_cart:
                    return Response({"message": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)

                cart_item = CartItems.objects.filter(id=pk, cart=active_cart).first()
                if not cart_item:
                    return Response({"message": "No such item found in the active cart."}, status=status.HTTP_404_NOT_FOUND)

                cart_item.delete()
                return Response({"message": "Item deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

            # If no pk is provided, delete the entire active cart
            instance = CartModel.objects.filter(user=request.user, is_ordered=False).first()
            if not instance:
                return Response({"message": "No active cart found."}, status=status.HTTP_404_NOT_FOUND)

            instance.delete()
            return Response({"message": "Cart deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response(
                {"message": "An unexpected error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderViews(APIView):

    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Place an order",
        operation_description="This endpoint places an order for the items in the user's active cart. It checks stock availability and updates the stock accordingly.",
        responses={
            200: openapi.Response("Order placed successfully"),
            400: "The cart is empty or insufficient stock for an item.",
            500: "An error occurred during the ordering process."
        }
    )
    def post(self,request,*args,**kwargs):
        try:

            active_cart=CartModel.objects.filter(user=request.user,is_ordered=False).first()

            if active_cart:
                cart_items=CartItems.objects.filter(cart=active_cart)
                if not cart_items.exists():
                    return Response({"message": "The cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

                for item in cart_items:
                    if item.quantity>item.book.stock:
                        return Response(
                        {"message": f"Insufficient stock for the book {item.book.name}."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    book = item.book
                    book.stock -= item.quantity
                    book.save()
                    
                active_cart.is_ordered = True
                active_cart.save()
                
                return Response({"message":"The order placed ","status":"Success"},status=status.HTTP_200_OK)
            
            return Response({"message": "No active cart to order."}, status=status.HTTP_400_BAD_REQUEST)
           
        except Exception as e:
            return Response(
                {"message": "An error occurred during the ordering process.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Retrieve order details",
        operation_description="This endpoint retrieves the orders placed by the authenticated user.",
        responses={
            200: openapi.Response("Order details fetched successfully"),
            404: "No orders found for the user.",
            500: "An error occurred while retrieving the orders."
        }
    )
    def get(self,request):
        try:
            ordered_cart=CartModel.objects.filter(user=request.user, is_ordered=True)

            if not ordered_cart.exists():
                return Response({"message": " No order Found","status":"Error"},status=status.HTTP_404_NOT_FOUND)
            
            serializer=CartSerializer(ordered_cart,many=True)
            return Response({"message": "Order details fetched successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"message": "An error occurred while retrieving the orders.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @swagger_auto_schema(
        operation_summary="Cancel an order",
        operation_description="This endpoint cancels the user's active order and restores the stock of the books in that order.",
        responses={
            200: "Order cancelled successfully.",
            404: "No order found to cancel.",
            500: "An error occurred while cancelling the order."
        }
    )
    def patch(self,request):
        try:
            ordered_cart=CartModel.objects.filter(user=request.user, is_ordered=True).first()
            if not ordered_cart:
                return Response({"message": "No order found to cancel."}, status=status.HTTP_404_NOT_FOUND)

            cart_items = CartItems.objects.filter(cart=ordered_cart)
            
            for item in cart_items:
                book=item.book
                book.stock+=item.quantity
                book.save()
            ordered_cart.delete()
            return Response({"message": "Order cancelled successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": "An error occurred while cancelling the order.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
