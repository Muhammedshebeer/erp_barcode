import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from .models import Product, StockEntry, Sale, SaleItem, Employee
from .forms import ProductForm, StockEntryForm, SaleForm, EmployeeForm
from .utils import generate_barcode_image, generate_barcodes_pdf
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from django.http import HttpResponse



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Use Django's authenticate function
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # sets session automatically

            Employee.objects.get_or_create(user=user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)  # clears Django session automatically
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
        product_id = request.POST.get("product_id")

        if not product_id:
            messages.error(request, "Please select a valid product.")
            return redirect("add_stock")

        product = Product.objects.get(id=product_id)

        # Convert fields properly
        qty = int(request.POST.get("qty"))
        purchase_price = request.POST.get("purchase_price") or 0

        # Create Stock Entry
        entry = StockEntry.objects.create(
            product=product,
            qty=qty,
            purchase_price=purchase_price,
            supplier_id=request.POST.get("supplier") or None,
            remarks=request.POST.get("remarks")
        )

        # Update product quantity
        product.quantity = product.quantity + qty
        product.save()

        return redirect('product_list')

    form = StockEntryForm()
    return render(request, 'add_stock.html', {'form': form})


def print_multiple_barcodes(request):
    products = Product.objects.all()

    if request.method != "POST":
        return render(request, "print_barcode.html", {"products": products})

    selected_ids = request.POST.getlist("product_ids")

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'inline; filename="barcodes.pdf"'

    c = canvas.Canvas(response, pagesize=A4)

    x = 10 * mm
    y = 270 * mm

    BARCODE_WIDTH = 38 * mm
    BARCODE_HEIGHT = 25 * mm
    GAP = 10 * mm

    for pid in selected_ids:
        p = Product.objects.get(id=pid)
        qty = int(request.POST.get(f"qty_{pid}", 1))

        for _ in range(qty):

            # Draw barcode
            c.drawImage(
                p.barcode_image.path,
                x, y,
                width=BARCODE_WIDTH,
                height=BARCODE_HEIGHT
            )

            # Draw text
            c.setFont("Helvetica", 8)


            # Move position
            y -= (BARCODE_HEIGHT + GAP)

            # New page when space ends
            if y < 20 * mm:
                c.showPage()
                y = 270 * mm

    c.save()
    return response

def product_search(request):
    q = request.GET.get('q', '')

    products = Product.objects.filter(
        Q(name__icontains=q) |
        Q(sku__icontains=q)
    )

    data = {
        "results": [
            {"id": p.id, "text": f"{p.name} ({p.sku})"}
            for p in products
        ]
    }

    return JsonResponse(data)

# @login_required
# @transaction.atomic
def create_sale(request):
    if request.method == "POST":
        sale_form = SaleForm(request.POST)
        if sale_form.is_valid():
            sale = sale_form.save(commit=False)
            if not sale.invoice_no:
                sale.invoice_no = f"INV{Sale.objects.count()+1:06d}"
            sale.total = Decimal('0.00')
            sale.save()

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

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    qty=qty,
                    price=price,
                    subtotal=subtotal
                )

                product.quantity -= qty
                product.save()

                sale.total += subtotal
                i += 1

            sale.save()
            return redirect('sale_detail',pk=sale.pk)
    else:
        sale_form = SaleForm()

    # Prepare products
    products_qs = Product.objects.all()
    products = list(products_qs.values('id', 'name', 'sale_price', 'barcode', 'quantity'))

    sales = Sale.objects.all().order_by('-created_at')  # newest first

    paginator = Paginator(sales, 10)  # 10 per page
    page_number = request.GET.get("page")
    sales_page = paginator.get_page(page_number)

    return render(request, 'create_sale.html', {
        'form': sale_form,
        'products': products,
        'sales': sales,
    })


def sale_pdf(request, pk):
    sale = Sale.objects.get(pk=pk)
    html = render_to_string('sale_pdf.html', {'sale': sale})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{sale.invoice_no}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response


def sale_detail_modal(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sale_detail_modal.html', {'sale': sale})

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

