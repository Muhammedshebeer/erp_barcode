from django import forms
from django.core.exceptions import ValidationError

from .models import Product, StockEntry, Sale, SaleItem, Employee


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


class EmployeeForm(forms.ModelForm):
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Employee
        fields = ['name', 'email', 'mob', 'username', 'password', 'confirm_password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise ValidationError("Passwords do not match!")