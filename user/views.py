from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import ShopRequest  # Import ShopRequest model
from django.views import View
from django.shortcuts import render, get_object_or_404
from shop.models import ShopDetails,Product, Order
from django.views.decorators.cache import never_cache
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.encoding import smart_str
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

@never_cache
@login_required
def indexfish(request):
    # Fetch all shop details
    shopdetails = ShopDetails.objects.all()
    
    context = {
        'shopdetails': shopdetails
    }
    return render(request, 'user/indexfish.html', context)

@never_cache
@login_required
def user_dashboard(request):
    user = request.user
    has_pending_shop_request = ShopRequest.objects.filter(user=user, status='pending').exists()
    
    context = {
        'user': user,
        'has_pending_shop_request': has_pending_shop_request,
    }
    
    response = render(request, 'user/user_dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def profile_completion(request):
    if request.method == 'POST':
        house_name = request.POST.get('house_name')
        city = request.POST.get('city')
        phone_number = request.POST.get('phone_number')
        postal_code = request.POST.get('postal_code')

        user = request.user
        user.house_name = house_name
        user.city = city
        user.contact = phone_number
        user.postal_code = postal_code
        user.save()

        return redirect('indexfish')  # Redirect to indexcattle view

    return render(request, 'user/profile_completion.html')

@never_cache
@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'user/profile_view.html', context)


@login_required
def profile_update(request):
    if request.method == 'POST':
        contact = request.POST.get('contact')
        house_name = request.POST.get('house_name')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')

        user = request.user
        user.contact = contact
        user.house_name = house_name
        user.city = city
        user.postal_code = postal_code
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('user:user_dashboard')
    
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'user/profile_update.html', context)

@never_cache
@login_required
def create_shop_request(request):
    # Check if the user already has a pending shop request
    existing_request = ShopRequest.objects.filter(user=request.user, status='pending').exists()

    if existing_request:
        messages.error(request, "You already have a pending shop request. Please wait for admin approval.")
        return redirect('user:user_dashboard')

    if request.method == 'POST':
        # Create a new shop request
        ShopRequest.objects.create(user=request.user, status='pending')
        messages.success(request, "Your shop request has been submitted successfully. Please wait for admin approval.")
        return redirect('user:user_dashboard')

    return render(request, 'user/create_shop_request.html')

class ShopDetailView(View):
    def get(self, request, id):
        shop = get_object_or_404(ShopDetails, id=id)  # Fetch the shop by ID
        return render(request, 'indexfish.html', {'shop': shop})  # Render the shop detail template

@login_required
def dashboard_content(request):
    return render(request, 'user/dashboard_content.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date', '-order_time').select_related('shop', 'address').prefetch_related('order_details__product')
    orders_data = [order.natural_key() for order in orders]
    return JsonResponse({'orders': json.dumps(orders_data, cls=DjangoJSONEncoder)})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))

    # Header
    elements.append(Paragraph("FishGrid", styles['Heading1']))
    elements.append(Paragraph("Your One-Stop Fish Shop", styles['Center']))
    elements.append(Spacer(1, 12))

    # Shop Info
    elements.append(Paragraph(f"Shop: {order.shop.shop_name}", styles['Heading3']))
    elements.append(Paragraph("123 Fish Street, Ocean City", styles['Normal']))
    elements.append(Paragraph("Phone: (123) 456-7890", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Invoice Title
    elements.append(Paragraph(f"INVOICE #{order.id}", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Customer Info
    elements.append(Paragraph("Bill To:", styles['Heading4']))
    elements.append(Paragraph(f"{order.address.name}", styles['Normal']))
    elements.append(Paragraph(f"{order.address.address}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Order Info
    elements.append(Paragraph(f"Order Date: {order.order_date}", styles['Normal']))
    elements.append(Paragraph(f"Order Time: {order.order_time}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Order Details Table
    data = [['Item', 'Quantity', 'Price', 'Total']]
    total = 0
    for item in order.order_details.all():
        item_total = item.quantity * item.price
        data.append([
            item.product.product_name,
            str(item.quantity),
            f"Rs. {item.price:.2f}",
            f"Rs. {item_total:.2f}"
        ])
        total += item_total

    data.append(['', '', 'Total:', f"Rs. {total:.2f}"])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Footer
    elements.append(Paragraph("Thank you for your purchase!", styles['Center']))
    elements.append(Paragraph("For any queries, please contact support@fishgrid.com", styles['Center']))

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    return response
