# inventory/utils.py
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings

def generate_barcodes_pdf(products):
    """
    Generates a PDF containing barcode images and product names for multiple products.
    Returns the path to the PDF file.
    """
    pdf_path = os.path.join(settings.MEDIA_ROOT, "barcodes_stickers.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)

    x, y = 50, 800  # starting position
    width, height = 150, 50  # barcode image size
    gap = 80  # vertical gap between barcodes

    for product in products:
        if not product.barcode_image:
            continue

        barcode_image_path = os.path.join(settings.MEDIA_ROOT, product.barcode_image.name)

        if os.path.exists(barcode_image_path):
            # Draw barcode image
            c.drawImage(barcode_image_path, x, y, width=width, height=height)

            # Draw product name under barcode
            c.drawString(x, y - 15, product.name)

            # Move to next position
            y -= gap
            if y < 50:
                c.showPage()
                y = 800

    c.save()
    return pdf_path
