from django.db import models
from django.urls import reverse
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField('SKU', max_length=10, unique=True, blank=True)  # will be auto-generated
    name = models.CharField(max_length=255)
    category = models.ForeignKey('Category', null=True, blank=True, on_delete=models.SET_NULL)
    supplier = models.ForeignKey('Supplier', null=True, blank=True, on_delete=models.SET_NULL)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    barcode = models.CharField(max_length=128, unique=True, blank=True, null=True)
    quantity = models.IntegerField(default=0)   # current stock
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.pk])

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not provided
        if not self.sku:
            last_product = Product.objects.order_by('-id').first()
            if last_product and last_product.sku.startswith('JW'):
                # extract the numeric part
                last_number = int(last_product.sku[2:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.sku = f"JW{str(new_number).zfill(8)}"  # pad with leading zeros: JW00000001
        super().save(*args, **kwargs)

class StockEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    qty = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"StockEntry {self.product} +{self.qty}"

class Sale(models.Model):
    invoice_no = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    customer_name = models.CharField(max_length=200, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale {self.invoice_no} - {self.created_at.date()}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # unit price at sale time
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.qty}"
