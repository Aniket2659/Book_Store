from django.urls import path
from .views import CartsViews,OrderViews

urlpatterns = [
    path('cart/', CartsViews.as_view(), name='cart'),  # URL for get, post, and delete requests on the cart
    path('order/', OrderViews.as_view(), name='order'),
    path('cart/<int:pk>/', CartsViews.as_view(), name='cart-item'), 
    ]
