import sqlite3
import random
import calendar
import os
from datetime import datetime, date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

DB_PATH = "meals.db"



# Create/connect to DB and table
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def get_monthly_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT customer_id, COUNT(DISTINCT DATE(timestamp)) AS meals_count
        FROM meals
        WHERE strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        GROUP BY customer_id
        ORDER BY meals_count DESC
    ''')
    stats = cursor.fetchall()
    conn.close()
    return stats


def log_meal_to_db(customer_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today().isoformat()
    cursor.execute('''
        SELECT COUNT(*) FROM meals
        WHERE customer_id = ? AND DATE(timestamp) = ?
    ''', (customer_id, today))

    already_logged = cursor.fetchone()[0]

    if already_logged:
        conn.close()
        return False  # Already logged today

    now = datetime.now().isoformat()
    cursor.execute('INSERT INTO meals (customer_id, timestamp) VALUES (?, ?)', (customer_id, now))
    conn.commit()
    conn.close()
    return True


def insert_fake_data(num_customers=30):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = date.today()
    year, month = today.year, today.month
    _, total_days = calendar.monthrange(year, month)

    for i in range(num_customers):
        customer_id = str(1000 + i)
        num_meals = random.randint(0, 30)
        available_days = list(range(1, total_days + 1))
        meal_days = random.sample(available_days, k=min(num_meals, total_days))

        for day_num in meal_days:
            day = date(year, month, day_num)
            timestamp = datetime.combine(day, datetime.min.time()) + timedelta(
                hours=random.randint(9, 14), minutes=random.randint(0, 59)
            )
            cursor.execute('''
                SELECT COUNT(*) FROM meals
                WHERE customer_id = ? AND DATE(timestamp) = ?
            ''', (customer_id, day.isoformat()))
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO meals (customer_id, timestamp) VALUES (?, ?)
                ''', (customer_id, timestamp.isoformat()))

    conn.commit()
    conn.close()


def clear_all_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals")
    conn.commit()
    conn.close()


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

    # Headers
    ws.append(["رقم الموظف", "عدد الوجبات"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Data rows
    for row in stats:
        ws.append(row)

    # Auto-size columns
    for col in ws.columns:
        max_length = max(len(str(cell.value)) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

    wb.save(file_path)
    return file_path