from django import forms
from .models import Product, StockEntry, Sale, SaleItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','name','category','supplier','cost_price','sale_price','barcode','quantity']

class StockEntryForm(forms.ModelForm):
    class Meta:
        model = StockEntry
        fields = ['product','qty','purchase_price','supplier','remarks']

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['invoice_no','customer_name']

# We'll handle sale items with JS; SaleItemForm used if needed for server-side validation
class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product','qty','price','subtotal']
