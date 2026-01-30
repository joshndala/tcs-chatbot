"""
Ingest Kaggle Customer Support Ticket Dataset into SQLite
"""
import pandas as pd
from pathlib import Path
import sys
import hashlib
import sqlite3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def generate_customer_id(name, email):
    """Generate a unique customer ID from name and email."""
    unique_string = f"{name}_{email}".lower()
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]


def ingest_customer_support_data():
    """Load Kaggle CSV data into SQLite database."""
    print("📊 Ingesting customer support ticket data...\n")
    
    try:
        # Find CSV file
        csv_path = Path("data/kaggle")
        csv_files = list(csv_path.glob("*.csv"))
        
        if not csv_files:
            print("❌ No CSV files found in data/kaggle/")
            print("Run 'python scripts/download_kaggle_data.py' first")
            return False
        
        # Read the CSV file
        df = pd.read_csv(csv_files[0])
        print(f"✓ Loaded {len(df)} rows from {csv_files[0].name}\n")
        
        # Generate customer IDs
        df['customer_id'] = df.apply(
            lambda row: generate_customer_id(row['Customer Name'], row['Customer Email']), 
            axis=1
        )
        
        # Extract unique customers
        customer_columns = [
            'customer_id', 'Customer Name', 'Customer Email',
            'Customer Age', 'Customer Gender', 'Product Purchased',
            'Date of Purchase'
        ]
        
        customers_df = df[customer_columns].drop_duplicates('customer_id')
        print(f"✓ Found {len(customers_df)} unique customers")
        
        # Connect to database
        db_path = settings.db_path
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Insert customers
        customer_count = 0
        for _, row in customers_df.iterrows():
            try:
                cursor.execute(
                    """INSERT OR IGNORE INTO customers 
                       (customer_id, customer_name, customer_email, customer_age, 
                        customer_gender, product_purchased, date_of_purchase)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row['customer_id'],
                        str(row['Customer Name']),
                        str(row['Customer Email']),
                        int(row['Customer Age']) if pd.notna(row['Customer Age']) else None,
                        str(row['Customer Gender']) if pd.notna(row['Customer Gender']) else None,
                        str(row['Product Purchased']) if pd.notna(row['Product Purchased']) else None,
                        str(row['Date of Purchase']) if pd.notna(row['Date of Purchase']) else None
                    )
                )
                customer_count += 1
            except Exception as e:
                print(f"Error inserting customer {row['customer_id']}: {e}")
        
        conn.commit()
        print(f"✓ Inserted {customer_count} customers")
        
        # Insert tickets
        ticket_count = 0
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    """INSERT INTO tickets 
                       (ticket_id, customer_id, ticket_type, ticket_subject, 
                        ticket_description, ticket_status, ticket_priority, 
                        ticket_channel, first_response_time, time_to_resolution,
                        customer_satisfaction_rating)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(row['Ticket ID']),
                        row['customer_id'],
                        str(row['Ticket Type']) if pd.notna(row['Ticket Type']) else None,
                        str(row['Ticket Subject']) if pd.notna(row['Ticket Subject']) else None,
                        str(row['Ticket Description']) if pd.notna(row['Ticket Description']) else None,
                        str(row['Ticket Status']) if pd.notna(row['Ticket Status']) else None,
                        str(row['Ticket Priority']) if pd.notna(row['Ticket Priority']) else None,
                        str(row['Ticket Channel']) if pd.notna(row['Ticket Channel']) else None,
                        str(row['First Response Time']) if pd.notna(row['First Response Time']) else None,
                        str(row['Time to Resolution']) if pd.notna(row['Time to Resolution']) else None,
                        float(row['Customer Satisfaction Rating']) if pd.notna(row['Customer Satisfaction Rating']) else None
                    )
                )
                ticket_count += 1
            except Exception as e:
                print(f"Error inserting ticket {row['Ticket ID']}: {e}")
                continue
        
        conn.commit()
        print(f"✓ Inserted {ticket_count} tickets")
        
        # Display summary
        print("\n✅ Data ingestion completed successfully!")
        print(f"\n📈 Database Summary:")
        
        cursor.execute('SELECT COUNT(*) as count FROM customers')
        customer_total = cursor.fetchone()[0]
        print(f"   - Customers: {customer_total}")
        
        cursor.execute('SELECT COUNT(*) as count FROM tickets')
        ticket_total = cursor.fetchone()[0]
        print(f"   - Tickets: {ticket_total}")
        
        # Show sample statistics
        cursor.execute('SELECT ticket_status, COUNT(*) as count FROM tickets GROUP BY ticket_status')
        status_counts = cursor.fetchall()
        print(f"\n📊 Ticket Status Breakdown:")
        for row in status_counts:
            print(f"   - {row[0]}: {row[1]}")
        
        cursor.execute('SELECT ticket_priority, COUNT(*) as count FROM tickets GROUP BY ticket_priority')
        priority_counts = cursor.fetchall()
        print(f"\n📊 Ticket Priority Breakdown:")
        for row in priority_counts:
            print(f"   - {row[0]}: {row[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = ingest_customer_support_data()
    sys.exit(0 if success else 1)
