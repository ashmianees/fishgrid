# models.py
from django.db import models
from django.conf import settings
from django.forms import ValidationError  # Import settings to access AUTH_USER_MODEL
from user.models import User
from django.contrib.auth.models import User

class ShopDetails(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    shop_name = models.CharField(max_length=255)
    shop_location = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    mobile_number = models.CharField(max_length=15)
    shop_image = models.ImageField(upload_to='shop_images/', null=True, blank=True)

    def __str__(self):
        return self.shop_name

class Category(models.Model):
    category_name = models.CharField(max_length=255, unique=True)  # Unique name for the category
    category_desc = models.TextField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)  # Add this line

    def clean(self):
        existing = Category.objects.filter(category_name__iexact=self.category_name).exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError('A category with this name already exists.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class Product(models.Model):
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)  # Product name
    product_description = models.TextField()  # Product description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price
    size = models.CharField(max_length=50, null=True, blank=True)  # New field for size
    quantity = models.IntegerField()  # Quantity
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)  # Foreign key to Category
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)  # Image field
    status = models.BooleanField(default=True)  # Status (active/inactive)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_price(self):
        total = sum(item.total_price() for item in self.items.all())
        return total

    def total_items(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)  # Add shop field
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} from {self.shop.shop_name}"

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product_name
    def __str__(self):
        return self.category_name

    def __str__(self):
        return self.shop_name


class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.product.product_name} by {self.user.username}"


from django.db import models
from django.conf import settings  # Import settings to use AUTH_USER_MODEL

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Update this line
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}, {self.address}, {self.phone}"


from django.db import models
from django.contrib.auth.models import User
from .models import ShopDetails, Address  # Ensure you import the necessary models

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)  # Foreign key to the ShopDetails model
    address = models.ForeignKey(Address, on_delete=models.CASCADE)  # Foreign key to the Address model
    order_date = models.DateField(auto_now_add=True)  # Automatically set the date when the order is created
    order_time = models.TimeField(auto_now_add=True)  # Automatically set the time when the order is created
    status = models.CharField(max_length=50, blank=True)  # Status of the order (e.g., 'Pending', 'Completed', 'Cancelled')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total price of the order

    def __str__(self):
        return f"Order {self.id} by {self.user.username} at {self.shop.shop_name} on {self.order_date} at {self.order_time}"

    def natural_key(self):
        return (self.id, self.shop.shop_name, self.order_date.isoformat(), self.order_time.isoformat(), self.total_price, self.status)

    class Meta:
        unique_together = (('id', 'shop'),)


from django.db import models
from .models import Order  # Ensure you import the necessary models

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)  # Add this line
    status = models.CharField(max_length=50, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} for Order {self.order.id} - Status: {self.status}"


class OrderDetails(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_details')  # Foreign key to Order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Foreign key to Product
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Field for price
    quantity = models.PositiveIntegerField()  # Field for quantity

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} pcs"
    
class Complaint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE) 
    complaint_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('resolved', 'Resolved'),
    ])

    def __str__(self):
        return f"Complaint by {self.user.username} for {self.shop.name}"

# Add this to your existing imports
from django.db import models
from django.conf import settings

# Add this new model at the end of the file
class CategoryRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=255)
    category_desc = models.TextField()
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ])
    reason = models.TextField(blank=True, null=True)  # Reason for rejection
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category_name} requested by {self.user.username}"

from django.contrib.auth.models import User

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)  # Assuming 'Product' is defined in the same app
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.product_name}"
