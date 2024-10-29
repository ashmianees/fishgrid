from django.http import Http404, JsonResponse
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from shop.models import Payment
import razorpay
from django.db.models import Q
from django.utils import timezone

from .models import Cart, CartItem, Category, Complaint, Wishlist
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from django.contrib import messages
from .models import Product, Feedback, ShopDetails

from .models import Product
from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import Cart, CartItem, Category, Complaint
from django.http import HttpResponseBadRequest
from .models import Product, Feedback, ShopDetails

from .models import Product
from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q
from .models import Cart, CartItem, Category, Complaint
from django.http import HttpResponseBadRequest

import logging
import json

logger = logging.getLogger(__name__)

def shop_product_views(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    categories = Category.objects.filter(is_active=True)
    selected_category = request.GET.get('category', '')
    
    # Filter out expired products
    products = Product.objects.filter(
        shop_id=shop_id,
        categories__is_active=True,
        status=True
    ).exclude(
        Q(expiry_date__isnull=False) & Q(expiry_date__lte=timezone.now().date())
    )
    
    if selected_category and selected_category.isdigit():
        products = products.filter(categories__id=selected_category)
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(product_description__icontains=search_query)
        )
    
    context = {
        'shop': shop,
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'shop/shop_product_views.html', context)

def view_singleproduct(request, product_id, shop_id):
    product = get_object_or_404(Product, id=product_id, shop__id=shop_id, categories__is_active=True)
    shop = product.shop
    
    # If user is not the shop owner and product is expired, return 404
    if request.user != shop.user and product.expiry_date and product.expiry_date <= timezone.now().date():
        raise Http404("Product not found")
        
    category = product.categories
    feedback = Feedback.objects.filter(product=product).order_by('-created_at')
    is_in_wishlist = False
    has_purchased = False

    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        has_purchased = Order.objects.filter(
            user=request.user,
            order_details__product=product
        ).exists()

    context = {
        'product': product,
        'category': category,
        'shop': shop,
        'feedback': feedback,
        'is_in_wishlist': is_in_wishlist,
        'has_purchased': has_purchased,
    }
    return render(request, 'shop/view_singleproduct.html', context)

from django.shortcuts import get_object_or_404, redirect
from .models import Product, Feedback, ShopDetails

from .models import Product
from .models import Product, ShopDetails
from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
def shop_index(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()  # Get the first shop detail
    else:
        shop_detail = None  # Handle the case where no shop details exist

    return render(request, 'shop/shop_index.html', {'shop_detail': shop_detail})  # Pass shop_detail to the template

@login_required  # Ensure the user is logged in
def shop_dashboard(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()  # Get the first shop detail
    else:
        shop_detail = None  # Handle the case where no shop details exist

    return render(request, 'shop/shop_index.html', {'shop_detail': shop_detail})  # Pass shop_detail to the template

@login_required
def shop_creation(request):
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name')
        shop_location = request.POST.get('shop_location')
        pincode = request.POST.get('pincode')
        mobile_number = request.POST.get('mobile_number')
        shop_image = request.FILES.get('shop_image')

        # Save the shop details to the database
        ShopDetails.objects.create(
            user=request.user,  # Associate the shop with the logged-in user
            shop_name=shop_name,
            shop_location=shop_location,
            pincode=pincode,
            mobile_number=mobile_number,
            shop_image=shop_image
        )

        return redirect('shop:shop_dashboard')  # Redirect to the shop dashboard after successful creation

    return render(request, 'shop/shop_creation.html') 


@login_required
def shop_profile_view(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()  # Get the first shop detail
    else:
        shop_detail = None  # Handle the case where no shop details exist

    return render(request, 'shop/shop_profile.html', {'shop_detail': shop_detail})

@login_required
def shop_details_edit(request, shop_id):
    # Retrieve the shop details for the given shop_id
    shop_details = get_object_or_404(ShopDetails, id=shop_id)

    if request.method == 'POST':
        # Get the updated values from the form
        shop_name = request.POST.get('shop_name')
        shop_location = request.POST.get('shop_location')
        owner_name = request.POST.get('owner_name')  # This is for display purposes
        mobile_number = request.POST.get('mobile_number')
        shop_image = request.FILES.get('shop_image')

        # Update the shop details
        shop_details.shop_name = shop_name
        shop_details.shop_location = shop_location
        shop_details.mobile_number = mobile_number

        # Update the shop image only if a new one is provided
        if shop_image:
            shop_details.shop_image = shop_image

        # Save the updated shop details to the database
        shop_details.save()

        # Redirect to the shop dashboard after successful update
        return redirect('shop_dashboard')  # Adjust this to your actual shop dashboard URL name

    # Render the edit shop template with the current shop details
    return render(request, 'shop/shop_details_edit.html', {'shop_details': shop_details})

from django.shortcuts import render, redirect, get_object_or_404

from .models import Cart, CartItem, Category, Complaint

def category_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, pk=shop_id)
    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'shop_detail': shop,
        'categories': categories,
    }
    return render(request, 'shop/shop_category.html', context)

def category_add(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_description = request.POST.get('category_description')  # Ensure this matches the form field name
        
        # Check if category_description is not None or empty
        if category_name and category_description:  # Ensure both fields are provided
            Category.objects.create(category_name=category_name, category_desc=category_description)
            return redirect('shop:shop_category')  # Redirect to the category list after adding
        else:
            # Handle the case where the fields are empty
            return render(request, 'shop/shop_category.html', {'error': 'Both fields are required.'})

    return render(request, 'shop/shop_category.html')  # Render the form if not a POST request

@csrf_exempt
def category_edit(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category_name = request.POST.get('category_name').strip()
        category_description = request.POST.get('category_description').strip()

        # Get the category instance to edit
        category = get_object_or_404(Category, id=category_id)

        # Update the category fields
        category.category_name = category_name
        category.category_desc = category_description
        category.save()

        # Redirect to the category page after successful update
        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'failed'}, status=400)

@require_POST
def category_delete(request):
    category_id = request.POST.get('id')
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return JsonResponse({'success': True})



from django.http import HttpResponseBadRequest


def product_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, pk=shop_id)
    products = Product.objects.filter(shop=shop)
    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'shop': shop,
        'products': products,
        'categories': categories,
    }
    return render(request, 'shop/shop_product.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


def product_add(request):
    try:
        shop_details = ShopDetails.objects.get(user=request.user)
    except ShopDetails.DoesNotExist:
        return HttpResponseBadRequest("Shop details not found for the user.")
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        description = request.POST.get('product_description')
        price = request.POST.get('product_price')
        size = request.POST.get('product_size')  # New field for size
        quantity = request.POST.get('product_quantity') 
        category_id = request.POST.get('product_category')  # New field for category
        image = request.FILES.get('product_image')
        expiry_date = request.POST.get('expire_date')  # Get expiry date from form
        
        if product_name and description and price and category_id:  # Basic validation
            category = Category.objects.get(id=category_id)  # Fetch the category by id
            
            # Create product with optional expiry date
            product = Product.objects.create(
                product_name=product_name,
                product_description=description,
                price=price,
                size=size,  # Include size
                quantity=quantity,
                categories=category,  # Associate with the category instance
                image=image,
                shop_id=shop_details.id,
                expiry_date=expiry_date if expiry_date else None  # Set expiry date if provided
            )
            return redirect('shop:product_list', shop_id=shop_details.id)  # Redirect to the product list with shop_id

    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    return render(request, 'shop/product_add.html', {'categories': categories})

def product_edit(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        product_name = request.POST.get('product_name')
        description = request.POST.get('product_description')
        price = request.POST.get('product_price')
        size = request.POST.get('product_size')
        quantity = request.POST.get('product_quantity')
        add_quantity = int(request.POST.get('add_quantity', 0))  # Get the additional quantity
        category_id = request.POST.get('product_category')
        image = request.FILES.get('product_image')
        expiry_date = request.POST.get('expire_date')

        if product_name and description and price and category_id:
            category = Category.objects.get(id=category_id)
            product.product_name = product_name
            product.product_description = description
            product.price = price
            product.size = size
            product.quantity = int(quantity) + add_quantity
            product.categories = category
            product.expiry_date = expiry_date if expiry_date else None
            if image:
                product.image = image
            product.save()

            return redirect('shop:product_list', shop_id=product.shop.id)

    categories = Category.objects.filter(is_active=True)
    return render(request, 'shop/shop_product.html', {'categories': categories})

def product_disable(request):
    product_id = request.GET.get('id')
    product = get_object_or_404(Product, pk=product_id)
    product.status = False  # Disable the product
    product.save()
    return redirect('shop:product_list')

from django.contrib import messages

@login_required
def add_to_cart(request, product_id, shop_id):
    logger.info(f"Add to cart called for product {product_id} and shop {shop_id}")
    if request.method == 'POST':
        try:
            cart, created = Cart.objects.get_or_create(user=request.user)
            product = get_object_or_404(Product, id=product_id)
            shop = get_object_or_404(ShopDetails, id=shop_id)

            quantity = int(request.POST.get('quantity', 1))
            logger.info(f"Attempting to add {quantity} of product {product.product_name} to cart")

            if quantity > product.quantity:
                logger.warning(f"Requested quantity {quantity} exceeds available stock {product.quantity}")
                messages.error(request, f"Sorry, only {product.quantity} items are available.")
                return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)

            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, shop=shop)

            if not created:
                cart_item.quantity += quantity
                logger.info(f"Updated existing cart item. New quantity: {cart_item.quantity}")
            else:
                cart_item.quantity = quantity
                logger.info(f"Created new cart item with quantity: {quantity}")
            cart_item.save()

            logger.info(f"Successfully added {quantity} {product.product_name}(s) to cart")
            messages.success(request, f"{quantity} {product.product_name}(s) added to cart.")
        except Product.DoesNotExist:
            logger.error(f"Product with id {product_id} not found")
            messages.error(request, "Product not found.")
        except ShopDetails.DoesNotExist:
            logger.error(f"Shop with id {shop_id} not found")
            messages.error(request, "Shop not found.")
        except Exception as e:
            logger.error(f"Error adding product to cart: {str(e)}")
            messages.error(request, f"Error adding product to cart: {str(e)}")

    return redirect('shop:view_cart')

@login_required
def view_cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.total_price() for item in cart_items)
        return render(request, 'shop/cart.html', {'items': cart_items, 'total_price': total_price})
    else:
        return render(request, 'shop/cart.html', {'items': [], 'total_price': 0})

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
        return redirect('shop:view_cart')





def submit_feedback(request, product_id, shop_id):
    if request.method == 'POST':
        shop = get_object_or_404(ShopDetails, id=shop_id)
        product = get_object_or_404(Product, id=product_id, shop=shop)
        rating = request.POST['rating']
        comment = request.POST['comment']
        Feedback.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, 'Your feedback has been submitted successfully.')
        return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)
    return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)

from .models import Product

def check_product_exists(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        shop_id = request.POST.get('shop_id')  # Get the shop ID from the request
        exists = Product.objects.filter(product_name=product_name, shop_id=shop_id).exists()  # Check in the specific shop
        return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})

from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails

@login_required
def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        shop_id = request.POST.get('shop_id')  # Get the shop ID from the request

        # Check if the product already exists in the shop
        if Product.objects.filter(product_name=product_name, shop_id=shop_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Product already exists in this shop.'})

        # Proceed to create the product if it does not exist
        shop = get_object_or_404(ShopDetails, id=shop_id)
        Product.objects.create(
            product_name=product_name,
            shop=shop,
            # Add other fields as necessary
        )
        return JsonResponse({'status': 'success', 'message': 'Product added successfully.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

from django.shortcuts import render, redirect, get_object_or_404

from .models import Address, Order, Cart, OrderDetails  # Ensure all necessary models are imported

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('shop:view_cart')

    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')
        
        if not selected_address_id:
            return JsonResponse({'status': 'error', 'message': 'Please select an address or add a new one.'})

        address = get_object_or_404(Address, id=selected_address_id, user=request.user)

        # Create the order
        order = Order.objects.create(
            user=request.user,
            shop=cart.items.first().shop,  # Assuming all items are from the same shop
            address=address,
            total_price=cart.total_price(),
            status='Pending'
        )

        # Create order details for each item in the cart
        for item in cart.items.all():
            OrderDetails.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
            # Update product quantity
            product = item.product
            product.quantity -= item.quantity
            product.save()

        # Clear the cart
        cart.items.all().delete()

        return JsonResponse({'status': 'success', 'message': 'Your order has been placed successfully!'})

    context = {
        'cart': cart,
        'addresses': addresses,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'shop/checkout.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Address  # Ensure this import is correct

@login_required  # Ensure the user is logged in
def add_new_address(request):
    if request.method == 'POST':
        new_name = request.POST.get('new_name')
        new_address = request.POST.get('new_address')
        new_phone = request.POST.get('new_phone')
        new_landmark = request.POST.get('new_landmark')
        new_pincode = request.POST.get('new_pincode')

        # Create and save the new address with the logged-in user
        address = Address.objects.create(
            user=request.user,  # Associate the address with the logged-in user
            name=new_name,
            address=new_address,
            phone=new_phone,
            landmark=new_landmark,
            pincode=new_pincode
        )

        return JsonResponse({
            'status': 'success',
            'message': 'New address added successfully!',
            'address_id': address.id,
            'name': address.name,
            'address': address.address,
            'phone': address.phone,
            'pincode': address.pincode
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

from django.shortcuts import render
from .models import Order


def order_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date', '-order_time')
    context = {
        'orders': orders,
        'category': {'shop_name': 'Fish Grid'},  # You can replace this with actual shop name logic if needed
    }
    return render(request, 'shop/Orders_view.html', context)

@login_required
def submit_complaint(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    
    # Check if the user has made a purchase from this shop
    has_purchased = Order.objects.filter(user=request.user, shop=shop).exists()

    if not has_purchased:
        messages.warning(request, "You can only submit a complaint if you have made a purchase from this shop.")
        return render(request, 'shop/complaints.html', {'shop': shop, 'has_purchased': has_purchased})

    if request.method == 'POST':
        complaint_text = request.POST.get('complaint_text')
        if complaint_text:
            Complaint.objects.create(
                user=request.user,
                shop=shop,
                complaint_text=complaint_text
            )
            messages.success(request, 'Your complaint has been submitted successfully.')
            return redirect('shop:shop_product_views', shop_id=shop.id)
        else:
            messages.error(request, 'Please enter your complaint.')

    return render(request, 'shop/complaints.html', {'shop': shop, 'has_purchased': has_purchased})

@login_required
def view_complaints(request, shop_id):
    # Fetch the shop details
    shop = get_object_or_404(ShopDetails, id=shop_id)
    
    # Fetch complaints related to the shop
    complaints = Complaint.objects.filter(shop=shop).order_by('-created_at')  # Order by creation date

    return render(request, 'shop/view_complaints.html', {'shop': shop, 'complaints': complaints})

@login_required
def order_success(request):
    return render(request, 'shop/order_success.html')


@login_required
def create_razorpay_order(request):
    if request.method == 'POST':
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            return JsonResponse({'status': 'error', 'message': 'Your cart is empty.'})

        total_price = cart.total_price()
        razorpay_order = razorpay_client.order.create({
            'amount': int(total_price * 100),  # Razorpay expects amount in paise
            'currency': 'INR',
            'payment_capture': '1'
        })

        return JsonResponse({
            'status': 'success',
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def create_order(request):
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        razorpay_order_id = request.POST.get('order_id')
        signature = request.POST.get('signature')

        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return JsonResponse({'status': 'error', 'message': 'Invalid payment signature'})

        # Create the order
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            return JsonResponse({'status': 'error', 'message': 'Your cart is empty.'})

        # Get the shop from the first item in the cart
        first_item = cart.items.first()
        if not first_item:
            return JsonResponse({'status': 'error', 'message': 'No items in cart.'})

        shop = first_item.shop

        address_id = request.POST.get('selected_address')
        address = get_object_or_404(Address, id=address_id, user=request.user)

        order = Order.objects.create(
            user=request.user,
            shop=shop,
            address=address,
            total_price=cart.total_price(),
            status='Paid'
        )

        for item in cart.items.all():
            # Check if there's enough stock
            if item.quantity > item.product.quantity:
                order.delete()  # Delete the order if there's not enough stock
                return JsonResponse({'status': 'error', 'message': f'Not enough stock for {item.product.product_name}'})

            OrderDetails.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            logger.info(f"Created OrderDetails for order {order.id}, product {item.product.id}, quantity {item.quantity}")

            # Update product quantity
            product = item.product
            product.quantity -= item.quantity
            product.save()
            logger.info(f"Updated stock for product {product.id}. New quantity: {product.quantity}")

        # Create payment record
        Payment.objects.create(
            order=order,
            payment_id=payment_id,
            amount=cart.total_price(),
            status='Completed'
        )

        # Clear the cart
        cart.delete()

        return JsonResponse({'status': 'success', 'message': 'Order placed successfully!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def filter_products(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    # Base query for products in this shop
    products = Product.objects.filter(shop=shop)
    
    # If user is not the shop owner, filter out disabled and expired products
    if request.user != shop.user:
        products = products.filter(
            status=True
        ).exclude(
            Q(expiry_date__isnull=False) & Q(expiry_date__lte=timezone.now().date())
        )
    
    # Apply search filter if provided
    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(product_description__icontains=search)
        )
    
    # Apply category filter if provided
    if category:
        products = products.filter(categories__id=category)
    
    products_data = [
        {
            'id': product.id,
            'name': product.product_name,
            'description': product.product_description,
            'price': str(product.price),
            'image': product.image.url if product.image else None,
            'shop_id': shop.id,
            'status': product.status,
            'is_expired': bool(product.expiry_date and product.expiry_date <= timezone.now().date()),
            'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else None
        }
        for product in products
    ]
    
    return JsonResponse({'products': products_data})

@login_required
def order_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id, user=request.user)
    orders = Order.objects.filter(shop=shop).order_by('-order_date', '-order_time')
    context = {
        'shop_detail': shop,
        'orders': orders,
    }
    return render(request, 'shop/order_list.html', context)

from .utils.ml_utils import get_product_recommendations, update_model_with_new_orders
from django.template.loader import render_to_string


@login_required
def product_recommendations(request):
    update_model_with_new_orders()
    shop = ShopDetails.objects.filter(user=request.user).first()
    if shop:
        recommended_products = get_product_recommendations(shop.id, limit=12)
    else:
        recommended_products = []
    context = {
        'recommended_products': recommended_products,
        'shop_detail': shop,  # Add this line
    }
    return render(request, 'shop/product_recommendations.html', context)

@login_required
def load_more_recommendations(request):
    offset = int(request.GET.get('offset', 0))
    shop = ShopDetails.objects.get(user=request.user)
    recommended_products = get_product_recommendations(shop.id, offset=offset, limit=6)
    html = render_to_string('shop/product_card.html', {'recommended_products': recommended_products})
    return JsonResponse({'html': html, 'count': len(recommended_products)})

@login_required
def add_product(request):
    try:
        shop_details = ShopDetails.objects.get(user=request.user)
    except ShopDetails.DoesNotExist:
        return HttpResponseBadRequest("Shop details not found for the user.")
    
    product_name = request.GET.get('product_name', '')
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        price = request.POST.get('price')
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id)
            Product.objects.create(
                shop=shop_details,
                product_name=product_name,
                product_description=product_description,
                price=price,
                size=size,
                quantity=quantity,
                categories=category,
                image=image
            )
            return redirect('shop:product_list', shop_id=shop_details.id)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'categories': categories,
        'shop_details': shop_details,
        'product_name': product_name
    }
    return render(request, 'shop/add_product.html', context)

from django.db.models import Prefetch

@login_required
def view_feedback_complaints(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id, user=request.user)
    
    # Fetch feedback for all products of this shop
    feedback = Feedback.objects.filter(product__shop=shop).order_by('-created_at').select_related('user', 'product').prefetch_related(
        Prefetch('user__order_set', queryset=Order.objects.filter(shop=shop).order_by('-order_date'), to_attr='shop_orders')
    )
    
    # Fetch complaints for this shop
    complaints = Complaint.objects.filter(shop=shop).order_by('-created_at').select_related('user').prefetch_related(
        Prefetch('user__order_set', queryset=Order.objects.filter(shop=shop).order_by('-order_date'), to_attr='shop_orders')
    )
    
    context = {
        'shop': shop,
        'shop_detail': shop,  # Add this line
        'feedback': feedback,
        'complaints': complaints,
    }
    return render(request, 'shop/view_feedback_complaints.html', context)


from .models import CategoryRequest

@login_required
def request_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_desc = request.POST.get('category_desc')
        CategoryRequest.objects.create(
            user=request.user,
            category_name=category_name,
            category_desc=category_desc
        )
        messages.success(request, 'Category request submitted successfully!')
        return redirect('shop:shop_index')
    return render(request, 'shop/request_category.html')

@login_required
def view_category_requests(request):
    category_requests = CategoryRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/view_category_requests.html', {'category_requests': category_requests})

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import redirect, get_object_or_404
from .models import Complaint

@login_required
def reply_to_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, shop__user=request.user)
    if request.method == 'POST':
        context = {
            'customer_name': complaint.user.get_full_name() or complaint.user.username,
            'shop_name': complaint.shop.shop_name,
            'complaint_id': complaint.id,
        }
        
        html_message = render_to_string('shop/email_templates/complaint_response.txt', context)
        plain_message = strip_tags(html_message)
        
        subject = f"Response to your complaint about {complaint.shop.shop_name}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [complaint.user.email]

        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            complaint.status = 'responded'
            complaint.save()
            messages.success(request, 'Reply sent successfully.')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')

    return redirect('shop:view_feedback_complaints', shop_id=complaint.shop.id)

import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CartItem, Cart
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

@require_POST
def update_cart_item(request):
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        logger.info(f"Updating cart item: {item_id} with quantity: {quantity}")
        
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        
        if quantity > cart_item.product.quantity:
            return JsonResponse({'success': False, 'error': 'Not enough stock available.'})
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'quantity': cart_item.quantity,
            'total_price': f"{cart_item.total_price():.2f}"
        })
    except CartItem.DoesNotExist:
        logger.error(f"Cart item not found: {item_id}")
        return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)
    except ValueError as e:
        logger.error(f"Invalid quantity value: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid quantity value.'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in update_cart_item: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)
    
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        
        # Calculate the new total price
        cart = Cart.objects.get(user=request.user)
        new_total_price = sum(item.total_price() for item in cart.items.all())
        
        return JsonResponse({
            'success': True, 
            'new_total_price': f"{new_total_price:.2f}",
            'items_count': cart.items.count()
        })
    except CartItem.DoesNotExist:
        logger.error(f"Cart item not found: {item_id}")
        return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while removing the item.'}, status=500)

@require_POST
def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)

    try:
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return JsonResponse({'success': True, 'action': 'removed'})
        else:
            return JsonResponse({'success': True, 'action': 'added'})

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        product__categories__is_active=True,
        product__status=True
    ).select_related('product')
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def toggle_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user == product.shop.user:
        product.status = not product.status
        product.save()
        action = "enabled" if product.status else "disabled"
        messages.success(request, f'Product {action} successfully.')
    else:
        messages.error(request, 'You do not have permission to perform this action.')
    return redirect('shop:product_list', shop_id=product.shop.id)




