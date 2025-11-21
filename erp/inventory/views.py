import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from .models import Product, StockEntry, Sale, SaleItem
from .forms import ProductForm, StockEntryForm, SaleForm
from .utils import generate_barcodes_pdf
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from .utils import generate_barcodes_pdf
from decimal import Decimal
from django.http import FileResponse

# @login_required
def dashboard(request):
    products_count = Product.objects.count()
    low_stock = Product.objects.filter(quantity__lt=5)
    recent_sales = Sale.objects.order_by('-created_at')[:5]
    return render(request, 'dashboard.html', {
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

# @login_required
def product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            # generate barcode image
            generate_barcode_image(product, settings.MEDIA_ROOT)
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'product_form.html', {'form': form})

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
                si = SaleItem(sale=sale, product=product, qty=qty, price=price, subtotal=subtotal)
                si.save()
                # reduce stock
                product.quantity -= qty
                product.save()
                sale.total += subtotal
                i += 1
            sale.save()
            return redirect('sale_detail', pk=sale.pk)
    else:
        sale_form = SaleForm()

    # 🔹 Convert products QuerySet to list of dictionaries for JSON serialization
    products_qs = Product.objects.all()
    products = list(products_qs.values('id', 'name', 'sale_price', 'barcode', 'quantity'))

    return render(request, 'create_sale.html',
                  {'form': sale_form, 'products': json.dumps(products, cls=DjangoJSONEncoder)})

# @login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sale_detail.html', {'sale': sale})

# @login_required
def lookup_by_barcode(request):
    """
    AJAX endpoint: ?barcode=XXXX -> returns JSON with product id, name, price, qty
    """
    barcode = request.GET.get('barcode')
    if not barcode:
        return JsonResponse({'ok': False, 'error': 'No barcode provided'}, status=400)
    try:
        product = Product.objects.get(barcode=barcode)
        return JsonResponse({
            'ok': True,
            'id': product.id,
            'name': product.name,
            'sale_price': str(product.sale_price),
            'quantity': product.quantity,
        })
    except Product.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Product not found'}, status=404)


def download_barcodes(request):
    products = Product.objects.all()
    pdf_path = generate_barcodes_pdf(products)
    return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename="barcodes_stickers.pdf")