from django.urls import path
from . import views
from .views import login_view, logout_view, sale_detail_modal

urlpatterns = [
    path('', login_view, name='login'),
    path('home', views.dashboard, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('dlt_products/<int:pk>/', views.delete_product, name='delete_product'),
    path('edit_product/', views.edit_product, name='edit_product'),

    path('sales/<int:pk>/pdf/', views.sale_pdf, name='sale_pdf'),
    path('logout/', logout_view, name='logout'),
    path('ajax/product-search/', views.product_search, name='product_search'),

    path('sales/<int:pk>/detail-modal/', sale_detail_modal, name='sale_detail_modal'),

    path('products/add/', views.product_add, name='product_add'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('sales/create/', views.create_sale, name='create_sale'),
    path('ajax/lookup-barcode/', views.lookup_barcode, name='lookup_barcode'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),

    path('barcodes/download/', views.download_barcodes, name='download_barcodes'),
]
