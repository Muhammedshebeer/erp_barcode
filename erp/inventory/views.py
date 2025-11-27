import json

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from .models import Product, StockEntry, Sale, SaleItem, Employee
from .forms import ProductForm, StockEntryForm, SaleForm, EmployeeForm
from .utils import generate_barcode_image, generate_barcodes_pdf

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
from django.http import FileResponse



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user = Employee.objects.get(username=username, password=password)
            request.session['user_id'] = user.id  # store session
            return redirect('home')

        except Employee.DoesNotExist:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()  # clears all session data
    return redirect('login')


def add_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'add_employee.html', {'form': form})

# @login_required
def dashboard(request):
    products_count = Product.objects.count()
    Product.objects.get(barcode="123456")
    print('barrr:',Product.name)
    low_stock = Product.objects.filter(quantity__lt=5)
    recent_sales = Sale.objects.order_by('-created_at')[:5]
    return render(request, 'home.html', {
        'products_count': products_count,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
    })

# @login_required
def product_list(request):
    q = request.GET.get('q','')
    products = Product.objects.all()
    if q:
        products = products.filter(name__icontains=q)
    return render(request, 'product_list.html', {'products': products, 'q': q})


def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            generate_barcode_image(product)
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form})

def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    return redirect('product_list')

def edit_product(request):
    if request.method == "POST":
        product_id = request.POST.get("id")
        product = get_object_or_404(Product, pk=product_id)

        product.name = request.POST.get("name")
        product.price = request.POST.get("price")
        # product.quantity = request.POST.get("quantity")
        product.save()

        return redirect("product_list")


# @login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

# @login_required
def add_stock(request):
    if request.method == "POST":
        form = StockEntryForm(request.POST)
        if form.is_valid():
            entry = form.save()
            # update product quantity
            p = entry.product
            p.quantity = p.quantity + entry.qty
            p.save()
            return redirect('product_list')
    else:
        form = StockEntryForm()
    return render(request, 'add_stock.html', {'form': form})

# @login_required
# @transaction.atomic
def create_sale(request):
    """
    Handles sale creation with dynamic items (item-product-0, item-qty-0, item-price-0, etc.)
    """
    if request.method == "POST":
        sale_form = SaleForm(request.POST)
        if sale_form.is_valid():
            sale = sale_form.save(commit=False)
            if not sale.invoice_no:
                sale.invoice_no = f"INV{Sale.objects.count()+1:06d}"
            sale.total = Decimal('0.00')
            sale.save()

            # parse sale items
            i = 0
            while True:
                pid = request.POST.get(f'item-product-{i}')
                qty = request.POST.get(f'item-qty-{i}')
                price = request.POST.get(f'item-price-{i}')
                if not pid:
                    break

                product = get_object_or_404(Product, pk=int(pid))
                qty = int(qty)
                price = Decimal(price)
                subtotal = price * qty

                # Create SaleItem
                si = SaleItem(
                    sale=sale,
                    product=product,
                    qty=qty,
                    price=price,
                    subtotal=subtotal
                )
                si.save()

                # Reduce stock
                product.quantity -= qty
                product.save()

                sale.total += subtotal
                i += 1

            sale.save()
            return redirect('sale_detail', pk=sale.pk)
    else:
        sale_form = SaleForm()

    # Prepare products data for JS (for dynamic rows & barcode lookup)
    products_qs = Product.objects.all()
    products = list(products_qs.values('id', 'name', 'sale_price', 'barcode', 'quantity'))

    return render(request, 'create_sale.html', {
        'form': sale_form,
        'products': products
    })
# @login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sale_details.html', {'sale': sale})

# @login_required
def lookup_barcode(request):
    """
    AJAX endpoint to search product by barcode
    """
    barcode = request.GET.get('barcode', '').strip()
    print('brr:',barcode)
    if not barcode:
        return JsonResponse({'ok': False, 'error': 'No barcode provided'})

    try:
        product = Product.objects.get(barcode=barcode)
        return JsonResponse({
            'ok': True,
            'id': product.id,
            'name': product.name,
            'sale_price': float(product.sale_price),
            'quantity': product.quantity,
        })
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Product not found'})


def download_barcodes(request):
    products = Product.objects.all()
    pdf_path = generate_barcodes_pdf(products)
    return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename="barcodes_stickers.pdf")

