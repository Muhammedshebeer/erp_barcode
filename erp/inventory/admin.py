from django.contrib import admin
from .models import Category, Supplier, Product, StockEntry, Sale, SaleItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name','contact','email')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku','name','category','quantity','sale_price')
    search_fields = ('sku','name','barcode')
    readonly_fields = ('barcode_image',)

@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = ('product','qty','purchase_price','created_at')

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    list_display = ('invoice_no','created_at','customer_name','total')
