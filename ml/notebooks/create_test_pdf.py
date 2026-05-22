from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# =============================================
# Creates sample bank statement PDFs
# for testing our forensics engine
#
# reportlab is a Python library for
# creating PDF files programmatically
# =============================================

def create_legitimate_pdf(filename):
    """
    Create a realistic LEGITIMATE bank statement PDF.
    Characteristics:
    → Odd salary amounts (TDS deducted)
    → Odd spending amounts (real purchases)
    → Natural balance fluctuation
    """

    # canvas.Canvas creates a new PDF file
    # letter = standard A4-ish page size (8.5 x 11 inches)
    c = canvas.Canvas(filename, pagesize=letter)

    # letter returns (width, height) in points
    # 1 point = 1/72 inch
    width, height = letter

    # ── Page Header ──
    # setFont(fontname, size) sets current font
    c.setFont("Helvetica-Bold", 16)

    # drawString(x, y, text)
    # x = distance from LEFT edge
    # y = distance from BOTTOM edge (PDF coordinates!)
    # Note: y=750 is near TOP of page (page is ~792 points tall)
    c.drawString(200, 750, "HDFC Bank Statement")

    c.setFont("Helvetica", 10)
    c.drawString(200, 730, "Account: XXXX1234")
    c.drawString(200, 715, "Period: Jan 2024 - Mar 2024")

    # ── Column Headers ──
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50,  680, "Date")
    c.drawString(150, 680, "Description")
    c.drawString(350, 680, "Amount")
    c.drawString(450, 680, "Balance")

    # Draw horizontal line under headers
    # line(x1, y1, x2, y2)
    c.line(50, 675, 550, 675)

    # ── Transaction Data ──
    # Legitimate transactions have ODD amounts
    # Notice salary varies each month (TDS deducted)
    transactions = [
        ("01/01/2024", "SALARY CREDIT",   "49342.00",  "49342.00"),
        ("02/01/2024", "UPI Payment",      "1847.00",   "47495.00"),
        ("05/01/2024", "Grocery Store",    "2341.00",   "45154.00"),
        ("08/01/2024", "Utility Bill",     "1823.00",   "43331.00"),
        ("10/01/2024", "ATM Withdrawal",   "3000.00",   "40331.00"),
        ("15/01/2024", "Online Purchase",  "4521.00",   "35810.00"),
        ("20/01/2024", "Restaurant",        "847.00",   "34963.00"),
        ("25/01/2024", "Fuel",             "2341.00",   "32622.00"),
        ("01/02/2024", "SALARY CREDIT",   "48891.00",  "81513.00"),
        ("03/02/2024", "Rent Payment",    "15000.00",   "66513.00"),
        ("07/02/2024", "Medical",          "2341.00",   "64172.00"),
        ("12/02/2024", "UPI Payment",      "1523.00",   "62649.00"),
        ("18/02/2024", "Grocery Store",    "3241.00",   "59408.00"),
        ("22/02/2024", "Online Purchase",  "5621.00",   "53787.00"),
        ("01/03/2024", "SALARY CREDIT",   "49124.00", "102911.00"),
    ]

    # Draw each transaction row
    c.setFont("Helvetica", 9)
    y = 660  # Start y position for first row

    for date, desc, amount, balance in transactions:
        # Draw each column at its x position
        c.drawString(50,  y, date)
        c.drawString(150, y, desc)
        c.drawString(350, y, amount)
        c.drawString(450, y, balance)
        y -= 20  # Move down 20 points for next row
                 # Negative because y goes UP in PDF coords

    # Save the PDF file
    c.save()
    print(f"✅ Created legitimate PDF: {filename}")


def create_fraudulent_pdf(filename):
    """
    Create a FRAUDULENT bank statement PDF.
    Characteristics:
    → Round salary (no TDS = fake)
    → Round spending amounts (manually typed)
    → Artificially high balance
    → Salary never varies
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, "HDFC Bank Statement")
    c.setFont("Helvetica", 10)
    c.drawString(200, 730, "Account: XXXX5678")
    c.drawString(200, 715, "Period: Jan 2024 - Mar 2024")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50,  680, "Date")
    c.drawString(150, 680, "Description")
    c.drawString(350, 680, "Amount")
    c.drawString(450, 680, "Balance")
    c.line(50, 675, 550, 675)

    # Fraudulent transactions — ALL round numbers!
    # Salary is ALWAYS exactly 75000 — no TDS variation
    transactions = [
        ("01/01/2024", "SALARY CREDIT",   "75000.00",   "75000.00"),
        ("02/01/2024", "UPI Payment",      "2000.00",    "73000.00"),
        ("05/01/2024", "Online Transfer",  "5000.00",    "68000.00"),
        ("08/01/2024", "ATM Withdrawal",   "3000.00",    "65000.00"),
        ("10/01/2024", "Online Purchase",  "2000.00",    "63000.00"),
        ("15/01/2024", "UPI Payment",      "1000.00",    "62000.00"),
        ("20/01/2024", "Online Transfer",  "5000.00",    "57000.00"),
        ("25/01/2024", "ATM Withdrawal",   "2000.00",    "55000.00"),
        ("01/02/2024", "SALARY CREDIT",   "75000.00",  "130000.00"),
        ("03/02/2024", "Rent Payment",    "15000.00",   "115000.00"),
        ("07/02/2024", "UPI Payment",      "5000.00",   "110000.00"),
        ("12/02/2024", "Online Transfer",  "3000.00",   "107000.00"),
        ("18/02/2024", "ATM Withdrawal",   "2000.00",   "105000.00"),
        ("22/02/2024", "Online Purchase",  "5000.00",   "100000.00"),
        ("01/03/2024", "SALARY CREDIT",   "75000.00",   "175000.00"),
    ]

    c.setFont("Helvetica", 9)
    y = 660

    for date, desc, amount, balance in transactions:
        c.drawString(50,  y, date)
        c.drawString(150, y, desc)
        c.drawString(350, y, amount)
        c.drawString(450, y, balance)
        y -= 20

    c.save()
    print(f"✅ Created fraudulent PDF: {filename}")


# ── Main execution ──
# os.makedirs creates folder if it doesn't exist
# exist_ok=True means no error if folder already exists
os.makedirs("data/test_pdfs", exist_ok=True)

create_legitimate_pdf("data/test_pdfs/legitimate_statement.pdf")
create_fraudulent_pdf("data/test_pdfs/fraudulent_statement.pdf")

print()
print("✅ Both test PDFs created in data/test_pdfs/")
print("   Now run test_forensics.py to analyze them!")