from django.urls import path
from . import views
from .views import login_view, logout_view

urlpatterns = [
    path('', login_view, name='login'),
    path('home', views.dashboard, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('dlt_products/<int:pk>/', views.delete_product, name='delete_product'),
    path('edit_product/', views.edit_product, name='edit_product'),


    path('logout/', logout_view, name='logout'),


    path('products/add/', views.product_add, name='product_add'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('sales/create/', views.create_sale, name='create_sale'),
    path('ajax/lookup-barcode/', views.lookup_barcode, name='lookup_barcode'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),  # assumes you have sale_detail view

    path('barcodes/download/', views.download_barcodes, name='download_barcodes'),
]
