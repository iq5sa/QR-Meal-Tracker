from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFileDialog, QComboBox
)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt
from datetime import datetime
import sys
import os

from casher_db import (
    init_db,
    insert_fake_orders,
    log_meal_to_db,
    export_monthly_stats_to_excel,
    get_monthly_stats,
    show_customers_and_alternates  # <-- Import the new function
)

bg_color = "#312f2f"
button_color = "#2b5797"


class StatsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("إحصائيات شهر محدد")
        self.setFixedSize(500, 500)
        self.setStyleSheet(f"background-color: {bg_color};")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("\ud83d\udcca إحصائيات الوجبات حسب الموظف"))

        # Month selection
        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet("font-size: 16px;")
        months = [f"{m:02d}" for m in range(1, 13)]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        layout.addWidget(QLabel("اختر الشهر:"))
        layout.addWidget(self.month_combo)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["رقم الموظف", "عدد الوجبات"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        export_button = QPushButton("\ud83d\udcc0 تصدير الإحصائيات إلى Excel")
        export_button.setStyleSheet(f"background-color: {button_color}; color: white;")
        export_button.clicked.connect(self.export_stats)
        layout.addWidget(export_button)

        alt_button = QPushButton("\ud83d\udc65 عرض المناوبين")
        alt_button.setStyleSheet(f"background-color: #e67e22; color: white;")
        alt_button.clicked.connect(self.show_alternates)
        layout.addWidget(alt_button)

        self.setLayout(layout)
        self.month_combo.currentIndexChanged.connect(self.load_data)
        self.load_data()

    def load_data(self):
        selected_month = self.month_combo.currentText()
        year = datetime.now().year
        from casher_db import create_connection
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT customers.code, COUNT(DISTINCT DATE(orders.created_at)) AS meals_count
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE strftime('%Y-%m', orders.created_at) = ?
            GROUP BY customers.code
            ORDER BY meals_count DESC
        ''', (f"{year}-{selected_month}",))
        data = cursor.fetchall()
        conn.close()
        self.table.setRowCount(len(data))
        for row_idx, (customer_id, count) in enumerate(data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(customer_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(count)))

    def export_stats(self):
        selected_month = self.month_combo.currentText()
        year = datetime.now().year
        filename = f"meal_stats_{year}-{selected_month}.xlsx"
        from casher_db import create_connection
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT customers.code, COUNT(DISTINCT DATE(orders.created_at)) AS meals_count
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE strftime('%Y-%m', orders.created_at) = ?
            GROUP BY customers.code
            ORDER BY meals_count DESC
        ''', (f"{year}-{selected_month}",))
        stats = cursor.fetchall()
        conn.close()

        export_folder = "exports"
        os.makedirs(export_folder, exist_ok=True)
        file_path = os.path.join(export_folder, filename)

        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
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

        # Add export date
        ws.append([])
        ws.append(["تاريخ تصدير الإحصائية", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

        wb.save(file_path)
        self.status_label.setText(f"\u2705 تم التصدير إلى:\n{file_path}\nتاريخ تصدير الإحصائية: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def show_alternates(self):
        # Show a dialog with customer and their مناوب
        alt_dialog = QDialog(self)
        alt_dialog.setWindowTitle("قائمة المناوبين")
        alt_dialog.setFixedSize(400, 400)
        alt_dialog.setStyleSheet(f"background-color: {bg_color};")
        layout = QVBoxLayout()
        label = QLabel("\ud83d\udc65 قائمة الموظفين ومناوبيهم")
        layout.addWidget(label)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["اسم الموظف", "اسم المناوب"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        # Get data from db_new
        conn_data = []
        try:
            import casher_db
            import io
            import sys as _sys
            old_stdout = _sys.stdout
            _sys.stdout = mystdout = io.StringIO()
            casher_db.show_customers_and_alternates()
            _sys.stdout = old_stdout
            lines = mystdout.getvalue().splitlines()[2:]  # skip header
            for line in lines:
                parts = line.split('|')
                if len(parts) == 2:
                    conn_data.append([parts[0].strip(), parts[1].strip()])
        except Exception as e:
            conn_data = [["خطأ", str(e)]]

        table.setRowCount(len(conn_data))
        for row_idx, (name, alt) in enumerate(conn_data):
            table.setItem(row_idx, 0, QTableWidgetItem(name))
            table.setItem(row_idx, 1, QTableWidgetItem(alt))

        alt_dialog.setLayout(layout)
        alt_dialog.exec()


class MealTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("برنامج تسجيل الوجبات")
        self.setFixedSize(800, 700)
        self.setStyleSheet(f"background-color: {bg_color};")

        main_layout = QVBoxLayout()

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo = QLabel()
            logo.setPixmap(QPixmap(logo_path).scaled(300, 85, Qt.KeepAspectRatio))
            logo.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(logo)

        title1 = QLabel("معهد التدريب النفطي / بيجي")
        title2 = QLabel("برنامج تسجيل استلام الوجبات")
        for title in [title1, title2]:
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
            main_layout.addWidget(title)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("رقم الموظف")
        self.entry.setAlignment(Qt.AlignRight)
        self.entry.setStyleSheet("padding: 12px; font-size: 16px; border: 1px solid #ccc;")
        main_layout.addWidget(self.entry)

        btn_log = QPushButton("\ud83d\udcdd تسجيل الوجبة")
        btn_log.setStyleSheet(f"background-color: #0078D7; color: white; padding: 10px; font-weight: bold;")
        btn_log.clicked.connect(self.log_meal)
        main_layout.addWidget(btn_log)

        btn_stats = QPushButton("\ud83d\udcca عرض الإحصائيات")
        btn_stats.setStyleSheet(f"background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        btn_stats.clicked.connect(self.show_stats)
        main_layout.addWidget(btn_stats)

        # Button to show today's orders
        btn_today = QPushButton("عرض طلبات اليوم")
        btn_today.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; font-weight: bold;")
        btn_today.clicked.connect(self.show_today_orders)
        main_layout.addWidget(btn_today)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #333;")
        main_layout.addWidget(self.status_label)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["رقم الموظف", "الوقت والتاريخ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)
        self.entry.setFocus()

    def log_meal(self):
        customer_id = self.entry.text().strip()
        if not customer_id:
            self.status_label.setText("يرجى إدخال رقم الموظف")
            self.status_label.setStyleSheet("color: orange;")
            return

        success = log_meal_to_db(customer_id)
        if success:
            self.table.insertRow(self.table.rowCount())
            self.table.setItem(self.table.rowCount()-1, 0, QTableWidgetItem(customer_id))
            self.table.setItem(self.table.rowCount()-1, 1, QTableWidgetItem(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.status_label.setText(f"\u2705 تم تسجيل الوجبة للزبون {customer_id}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"\u26a0️ الموظف {customer_id} تم تسجيله اليوم بالفعل أو الرقم غير صحيح")
            self.status_label.setStyleSheet("color: red;")

        self.entry.clear()
        self.entry.setFocus()

    def show_stats(self):
        dialog = StatsDialog()
        dialog.exec()

    def show_today_orders(self):
        from casher_db import create_connection
        conn = create_connection()
        cursor = conn.cursor()
        today = datetime.now().date().isoformat()
        cursor.execute('''
            SELECT customers.code, customers.name, orders.created_at
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE DATE(orders.created_at) = ?
            ORDER BY orders.created_at DESC
        ''', (today,))
        rows = cursor.fetchall()
        conn.close()

        dialog = QDialog(self)
        dialog.setWindowTitle("طلبات اليوم")
        dialog.setFixedSize(500, 400)
        dialog.setStyleSheet(f"background-color: {bg_color};")
        layout = QVBoxLayout()
        label = QLabel("طلبات اليوم")
        layout.addWidget(label)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["رقم الموظف", "اسم الموظف", "الوقت والتاريخ"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        table.setRowCount(len(rows))
        for row_idx, (code, name, created_at) in enumerate(rows):
            table.setItem(row_idx, 0, QTableWidgetItem(str(code)))
            table.setItem(row_idx, 1, QTableWidgetItem(str(name)))
            table.setItem(row_idx, 2, QTableWidgetItem(str(created_at)))

        dialog.setLayout(layout)
        dialog.exec()


if __name__ == "__main__":
    init_db()
    insert_fake_orders()  # <-- Insert some fake orders for testing
    app = QApplication(sys.argv)
    window = MealTrackerApp()
    window.show()
    sys.exit(app.exec())