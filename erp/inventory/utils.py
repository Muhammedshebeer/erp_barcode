# inventory/utils.py
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from barcode import Code128
from barcode.writer import ImageWriter
from django.conf import settings


def generate_barcode_image(product):
    print("DEBUG: Starting barcode generation...")
    print("DEBUG: Product ID:", product.id)
    print("DEBUG: Product barcode:", product.barcode)

    from barcode import Code128
    from barcode.writer import ImageWriter

    folder = os.path.join(settings.MEDIA_ROOT, "barcodes")
    os.makedirs(folder, exist_ok=True)

    filename = f"{product.id}.png"
    filepath = os.path.join(folder, filename)

    try:
        print("DEBUG: Creating barcode object...")
        barcode = Code128(str(product.barcode), writer=ImageWriter())

        print("DEBUG: Saving barcode file:", filepath)
        barcode.save(filepath.replace('.png', ''))

        print("DEBUG: Updating product.barcode_image")
        product.barcode_image.name = f"barcodes/{filename}"
        product.save()

        print("DEBUG: DONE — barcode generated successfully!")

    except Exception as e:
        print("ERROR generating barcode:", e)



def generate_barcodes_pdf(products):
    """
    Generates a PDF containing barcode images and product names.
    Returns the path to the PDF file.
    """
    pdf_path = os.path.join(settings.MEDIA_ROOT, "barcodes_stickers.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)

    x, y = 40, 780
    width, height = 250, 120
    gap = 150

    for product in products:
        if not product.barcode_image:
            continue

        barcode_image_path = os.path.join(settings.MEDIA_ROOT, product.barcode_image.name)

        if os.path.exists(barcode_image_path):
            c.drawImage(barcode_image_path, x, y, width=width, height=height, preserveAspectRatio=True)
            c.setFont("Helvetica", 12)
            c.drawString(x, y - 20, product.name)

            y -= gap
            if y < 100:
                c.showPage()
                y = 780

    c.save()
    return pdf_path
