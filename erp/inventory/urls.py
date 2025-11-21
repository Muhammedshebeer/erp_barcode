from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('sales/create/', views.create_sale, name='create_sale'),
    path('sale/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('ajax/lookup-barcode/', views.lookup_by_barcode, name='lookup_by_barcode'),
    path('barcodes/download/', views.download_barcodes, name='download_barcodes'),
]
