from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import ModelSelect2Widget, Select2Widget
from .models import Product, StockEntry, Sale, SaleItem, Employee


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku','name','category','supplier','cost_price','sale_price','barcode','quantity']

class StockEntryForm(forms.ModelForm):
    product_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = StockEntry
        fields = ['product', 'qty', 'purchase_price', 'supplier', 'remarks']
        widgets = {
            'product': Select2Widget(attrs={'style': 'width:100%'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a label showing name and SKU in the dropdown
        self.fields['product'].queryset = Product.objects.all()
        self.fields['product'].label_from_instance = lambda obj: f"{obj.name} ({obj.sku})"


def product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) | Product.objects.filter(sku__icontains=query)
    results = []

    for p in products[:10]:  # limit results
        results.append({
            'id': p.id,
            'text': f"{p.name} ({p.sku})"
        })

    return JsonResponse({'results': results})

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
    class Meta:
        model = Employee
        fields = ['name', 'email', 'mob', 'image', 'age', 'address']

