import csv
import sqlite3
import random
import calendar
import os
from datetime import datetime, date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

DB_PATH = "db/meal_tracker.db"


def create_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = create_connection()
    cursor = conn.cursor()

    # Create customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL CHECK(length(code) = 6),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create alternates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alternates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL UNIQUE,
            alternates_customer_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (alternates_customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    # Optional index for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)")

    conn.commit()
    conn.close()


def add_customer(name, code):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customers (name, code)
        VALUES (?, ?)
    ''', (name, code))
    conn.commit()
    conn.close()


def get_customer_id_by_code(code):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM customers WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def insert_alternate(customer_code, alternate_code):
    conn = create_connection()
    cursor = conn.cursor()
    customer_id = get_customer_id_by_code(customer_code)
    alternate_id = get_customer_id_by_code(alternate_code)
    if customer_id and alternate_id:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO alternates (customer_id, alternates_customer_id) VALUES (?, ?)",
                (customer_id, alternate_id)
            )
            conn.commit()
        except Exception as e:
            print(f"❌ Error inserting alternate: {e}")
    conn.close()


def log_meal_to_db(customer_code):
    customer_id = get_customer_id_by_code(customer_code)
    if not customer_id:
        return False  # Invalid code

    conn = create_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    cursor.execute('''
        SELECT COUNT(*) FROM orders
        WHERE customer_id = ? AND DATE(created_at) = ?
    ''', (customer_id, today))

    already_logged = cursor.fetchone()[0]

    if already_logged:
        conn.close()
        return False

    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO orders (customer_id, created_at)
        VALUES (?, ?)
    ''', (customer_id, now))
    conn.commit()
    conn.close()
    return True


def get_monthly_stats():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT customers.code, COUNT(DISTINCT DATE(orders.created_at)) AS meals_count
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        WHERE strftime('%Y-%m', orders.created_at) = strftime('%Y-%m', 'now')
        GROUP BY customers.code
        ORDER BY meals_count DESC
    ''')
    stats = cursor.fetchall()
    conn.close()
    return stats


def export_monthly_stats_to_excel(filename=None):
    stats = get_monthly_stats()
    year_month = date.today().strftime("%Y-%m")
    if not filename:
        filename = f"meal_stats_{year_month}.xlsx"

    export_folder = "exports"
    os.makedirs(export_folder, exist_ok=True)
    file_path = os.path.join(export_folder, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = "الإحصائيات الشهرية"

    ws.append(["كود الموظف", "عدد الوجبات"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for row in stats:
        ws.append(row)

    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    wb.save(file_path)
    return file_path




def import_customers_from_csv(csv_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO customers (name, code)
                    VALUES (?, ?)
                ''', (row['name'], row['code']))
                count += 1
            except sqlite3.Error as e:
                print(f"Error with row {row}: {e}")

    conn.commit()
    conn.close()
    print(f"{count} customers imported from CSV.")


def clear_all_data():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM alternates")
    cursor.execute("DELETE FROM customers")
    conn.commit()
    conn.close()


def show_customers_and_alternates():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c1.name AS customer, c2.name AS alternate
        FROM customers c1
        LEFT JOIN alternates a ON c1.id = a.customer_id
        LEFT JOIN customers c2 ON a.alternates_customer_id = c2.id
        ORDER BY c1.name
    ''')
    rows = cursor.fetchall()
    print("Customer Name | Alternate Name")
    print("-------------------------------")
    for customer, alternate in rows:
        print(f"{customer} | {alternate if alternate else 'No alternate'}")
    conn.close()


def insert_fake_orders(num_orders=50):
    """
    Insert fake orders for random customers on random dates in the current month.
    """
    conn = create_connection()
    cursor = conn.cursor()

    # Get all customer ids
    cursor.execute("SELECT id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    if not customer_ids:
        print("No customers found to insert orders.")
        conn.close()
        return

    today = date.today()
    year, month = today.year, today.month
    _, total_days = calendar.monthrange(year, month)

    for _ in range(num_orders):
        customer_id = random.choice(customer_ids)
        day = random.randint(1, total_days)
        hour = random.randint(8, 15)
        minute = random.randint(0, 59)
        fake_datetime = datetime(year, month, day, hour, minute)
        cursor.execute(
            "INSERT INTO orders (customer_id, created_at) VALUES (?, ?)",
            (customer_id, fake_datetime.isoformat())
        )

    conn.commit()
    conn.close()
    print(f"Inserted {num_orders} fake orders for random customers.")


