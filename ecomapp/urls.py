from django.contrib import admin
from ecomapp import views
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)

urlpatterns = [
    path('', views.getRoutes, name='getRoutes'),
    path('products/', views.getProducts, name='products'),
    path('products/<int:pk>/', views.getProduct, name='product'),
    path('cart/', views.getCart, name='getCart'),
    path('cart/add/', views.addToCart, name='addToCart'),
    path('cart/remove/<int:cart_id>/', views.removeFromCart, name='removeFromCart'),
    path('orders/', views.getOrders, name='getOrders'),
    path('orders/place/', views.placeOrder, name='placeOrder'),
    path('payment/create/', views.createPayment, name='createPayment'),
    path('users/login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/profile/', views.getUserProfiles, name='getUserProfiles'),
    path('users/', views.getUsers, name='getUsers'),
    path('users/register/', views.registerUser, name="register"),
    path('activate/<uidb64>/<token>', views.ActivateAccountView.as_view(), name='activate'),

    # Coupon-related endpoints
    path('coupons/', views.get_available_coupons, name="get_coupons"),
    path('coupons/validate/', views.validate_coupon, name="validate_coupon"),

    path('categories/', views.getCategories, name='categories'),
    path('categories/<int:pk>/', views.getCategory, name='category-detail'),
    
    path('addresses/', views.get_addresses, name='get_addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/update/<int:address_id>/', views.update_address, name='update_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
]