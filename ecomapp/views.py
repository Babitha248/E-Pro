from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny

# from django_filters.rest_framework import DjangoFilterBackend


# from .products import products
from .models import Cart, Order, OrderItem, Products, Coupon, CouponUsage, Category, Address
from .serializer import ProductSerializer, UserSerializer, UserSerializerWithToken, CartSerializer, OrderSerializer, CategorySerializer, CouponSerializer, AddressSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer 
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import status
# from rest_framework import generics

# for sending mails and generate token
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from .utils import TokenGenerator, generate_token
from django.utils.encoding import force_str, force_bytes  # Update the import statement for force_text


# ... existing code ...from django.core.mail import EmailMessage
from django.conf import settings
from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# import stripe
from django.conf import settings
from django.utils import timezone


# import threading


# class EmailThread(threading.Thread):
#     def __init__(self, email_message):
#         self.email_message=email_message
#         threading.Thread.__init__(self)
#     def run(self):
#         self.email_message.send()

# Create your views here.
@api_view(['GET'])
def getRoutes(request):
    return Response("Hello World")
@api_view(['GET'])
def getCategories(request):
    try:
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def getCategory(request, pk):
    try:
        category = Category.objects.get(id=pk)
        serializer = CategorySerializer(category, context={'request': request})
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

      


@api_view(['GET'])
def getProducts(request):
    subcategory = request.query_params.get('subcategory', None)
    products = Products.objects.filter(is_active=True)
    
    if subcategory:
        products = products.filter(subcategory_id=subcategory)
    
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getProduct(request, pk):
    try:
        product = Products.objects.get(_id=pk)
        # Check if product is active
        if not product.is_active:
            return Response({'detail': 'Product is not available'}, 
                          status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, many=False)
        return Response(serializer.data)
    except Products.DoesNotExist:
        return Response({'detail': 'Product not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in getProduct: {str(e)}")
        return Response({'detail': str(e)}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getCart(request):
    print("Authenticated User:", request.user)
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items.exists():
        return Response({"message": "Cart is empty"}, status=status.HTTP_200_OK)
    
    serializer = CartSerializer(cart_items, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addToCart(request):
    user = request.user
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)

    try:
        product = get_object_or_404(Products, _id=product_id)
        cart_item, created = Cart.objects.get_or_create(user=user, product=product)
        if not created:
            cart_item.quantity += int(quantity)
        cart_item.save()
        return Response({"message": "Item added to cart"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def removeFromCart(request, cart_id):
    try:
        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def placeOrder(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

    total_price = sum(item.product.price * item.quantity for item in cart_items)
    order = Order.objects.create(user=user, total_price=total_price, is_paid=False)

    for item in cart_items:
        OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        item.delete()

    return Response({"message": "Order placed successfully", "order_id": order.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrders(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


# stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createPayment(request):
    user = request.user
    order_id = request.data.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=user)

    if order.is_paid:
        return Response({"error": "Order is already paid"}, status=status.HTTP_400_BAD_REQUEST)

    intent = stripe.PaymentIntent.create(
        amount=int(order.total_price * 100),
        currency="usd",
        metadata={"order_id": order.id}
    )

    return Response({"client_secret": intent["client_secret"]})

# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         serializer = UserSerializerWithToken(self.user).data
#         data.update(serializer)
#         return data

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print("Login Attempt with:", attrs)
        data = super().validate(attrs)  # Parent class handles authentication
        print("Token Data:", data)
        serializer = UserSerializerWithToken(self.user).data
        print("User Serializer Data:", serializer)
        for k, v in serializer.items():
            data[k] = v
        return data

    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfiles(request):
    user=request.user
    serializer=UserSerializer(user, many=False)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    user =User.objects.all() # Fetch all user objects
    serializer = UserSerializer(user, many=True)  # Serialize the queryset
    return Response(serializer.data)

@api_view(['POST'])
def registerUser(request):
    data = request.data
    print("Received registration data:", data)
    
    try:
        # Validate required fields
        required_fields = ['fname', 'lname', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if user exists
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'User with this email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create user
            user = User.objects.create(
                first_name=data['fname'],
                last_name=data['lname'],
                username=data['email'],
                email=data['email'],
                password=make_password(data['password']),
                is_active=True,  # Set to True for now to skip email verification
            )
            
            print(f"User created successfully with ID: {user.id}")

            # For development, skip email sending
            serializer = UserSerializerWithToken(user, many=False)
            return Response({
                'success': True,
                'message': 'Registration successful!',
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)

            # Once email is configured, uncomment this block
            '''
            try:
                email_subject = "Activate Your Account"
                message = render_to_string(
                    "activate.html",
                    {
                        'user': user,
                        'domain': '127.0.0.1:8000',
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': generate_token.make_token(user)
                    }
                )

                email_message = EmailMessage(
                    email_subject, 
                    message, 
                    settings.EMAIL_HOST_USER, 
                    [data['email']]
                )
                email_message.send()
                print(f"Activation email sent to: {data['email']}")

                serializer = UserSerializerWithToken(user, many=False)
                return Response({
                    'success': True,
                    'message': 'Registration successful! Please check your email to activate your account.',
                    'user': serializer.data
                }, status=status.HTTP_201_CREATED)

            except Exception as email_error:
                print(f"Error sending activation email: {str(email_error)}")
                user.delete()
                return Response({
                    'error': 'Failed to send activation email. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            '''

        except Exception as user_create_error:
            print(f"Error creating user: {str(user_create_error)}")
            return Response({
                'error': 'Failed to create user account. Please try again.'
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        print(f"Unexpected registration error: {str(e)}")
        return Response({
            'error': 'An unexpected error occurred during registration. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)
        except Exception as e:
            user = None
        
        if user is not None and generate_token.check_token(user, token):
            user.is_active = True
            user.save()
            message = "Account is Activated."
            return HttpResponse(message, status=200)
        else:
            return HttpResponse("Invalid activation link.", status=400)
            
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_coupon(request):
    code = request.data.get('code')
    cart_total = request.data.get('cart_total')

    if not code or not cart_total:
        return Response({'error': 'Coupon code and cart total are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        coupon = Coupon.objects.get(
            code=code,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now()
        )

        # Check usage limit
        if coupon.usage_limit > 0 and coupon.times_used >= coupon.usage_limit:
            return Response({'error': 'Coupon usage limit exceeded'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has already used this coupon
        if CouponUsage.objects.filter(coupon=coupon, user=request.user).exists():
            return Response({'error': 'You have already used this coupon'}, status=status.HTTP_400_BAD_REQUEST)

        # Check minimum purchase requirement
        cart_total = float(cart_total)
        if cart_total < float(coupon.minimum_purchase):
            return Response({'error': f'Minimum purchase of ${coupon.minimum_purchase} required'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate discount
        discount_amount = (cart_total * (float(coupon.discount_value) / 100)) if coupon.discount_type == 'percentage' else float(coupon.discount_value)

        return Response({
            'success': True,
            'discount_amount': round(discount_amount, 2),
            'coupon_id': coupon.id
        }, status=status.HTTP_200_OK)

    except Coupon.DoesNotExist:
        return Response({'error': 'Invalid coupon code'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated users to fetch available coupons
def get_available_coupons(request):
    try:
        coupons = Coupon.objects.filter(
            is_active=True, 
            valid_from__lte=timezone.now(), 
            valid_until__gte=timezone.now()
        ).values('id', 'code', 'discount_type', 'discount_value', 'minimum_purchase')
        
        return Response({'success': True, 'coupons': list(coupons)}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_coupons(request):
    coupons = Coupon.objects.all()
    serializer = CouponSerializer(coupons, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    serializer = AddressSerializer(addresses, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_address(request):
    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)  # Ensure the address belongs to the user
    except Address.DoesNotExist:
        return Response({'detail': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AddressSerializer(address, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)  # Ensure the address belongs to the user
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Address.DoesNotExist:
        return Response({'detail': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
          
            