
"""
Migration script to add subtotal, gst_amount, total, and modified_after_arn 
columns to existing Invoice table and populate them with calculated values.

Run this script ONCE after updating your models.py
"""
from models import db, Invoice
from utils import recalculate_invoice_totals

def migrate():
    print("Starting migration...")
    
    # Add new columns if they don't exist
    try:
        db.execute_sql("""
            ALTER TABLE invoice ADD COLUMN subtotal REAL DEFAULT 0 CHECK(subtotal >= 0)
        """)
        print("✓ Added subtotal column")
    except Exception as e:
        print(f"  subtotal column already exists or error: {e}")
    
    try:
        db.execute_sql("""
            ALTER TABLE invoice ADD COLUMN gst_amount REAL DEFAULT 0 CHECK(gst_amount >= 0)
        """)
        print("✓ Added gst_amount column")
    except Exception as e:
        print(f"  gst_amount column already exists or error: {e}")
    
    try:
        db.execute_sql("""
            ALTER TABLE invoice ADD COLUMN total REAL DEFAULT 0 CHECK(total >= 0)
        """)
        print("✓ Added total column")
    except Exception as e:
        print(f"  total column already exists or error: {e}")
    
    try:
        db.execute_sql("""
            ALTER TABLE invoice ADD COLUMN modified_after_arn INTEGER DEFAULT 0
        """)
        print("✓ Added modified_after_arn column")
    except Exception as e:
        print(f"  modified_after_arn column already exists or error: {e}")
    
    # Populate existing invoices with calculated values
    print("\nRecalculating totals for existing invoices...")
    invoices = Invoice.select()
    count = 0
    
    for invoice in invoices:
        try:
            recalculate_invoice_totals(invoice)
            count += 1
            print(f"  ✓ Invoice #{invoice.id}: subtotal={invoice.subtotal}, gst={invoice.gst_amount}, total={invoice.total}")
        except Exception as e:
            print(f"  ✗ Error processing invoice #{invoice.id}: {e}")
    
    print(f"\n✅ Migration complete! Updated {count} invoices.")
    print("\nYou can now:")
    print("1. View invoices via API: GET /invoices/<id>")
    print("2. Edit invoices: GET /invoices_page/edit/<id>")
    print("3. All totals are now stored in the database")

if __name__ == "__main__":
    migrate()