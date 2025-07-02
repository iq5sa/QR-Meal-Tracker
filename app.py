import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from PIL import Image, ImageTk
from datetime import datetime
import os

from db import (
    init_db,
    log_meal_to_db,
    insert_fake_data,
    clear_all_data,
    export_monthly_stats_to_excel,
    get_monthly_stats
)


# ---------- Functions ----------

def log_meal():
    customer_id = entry_customer_id.get().strip()
    if not customer_id:
        return

    success = log_meal_to_db(customer_id)
    if success:
        table.insert('', 'end', values=(customer_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        status_label.config(text=f"✅ تم تسجيل الوجبة للزبون {customer_id}.", fg="green")
    else:
        status_label.config(text=f"⚠️ الموظف {customer_id} تم تسجيله اليوم بالفعل.", fg="red")

    entry_customer_id.delete(0, tk.END)
    entry_customer_id.focus()

def show_stats():
    stats_window = tk.Toplevel(root)
    stats_window.title("إحصائيات الشهر الحالي")
    stats_window.geometry("400x400")
    stats_window.configure(bg=bg_color)

    tk.Label(stats_window, text="📊 إحصائيات الوجبات حسب الموظف", font=title_font, bg=bg_color).pack(pady=10)

    stats_table = ttk.Treeview(stats_window, columns=("ID", "Meals"), show='headings')
    stats_table.heading("ID", text="رقم الموظف")
    stats_table.heading("Meals", text="عدد الوجبات")
    stats_table.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    for customer_id, count in get_monthly_stats():
        stats_table.insert('', 'end', values=(customer_id, count))

    status_export = tk.Label(stats_window, text="", font=body_font, bg=bg_color)
    status_export.pack(pady=(5, 0))

    def export_stats():
        try:
            file_path = export_monthly_stats_to_excel()
            status_export.config(
                text=f"✅ تم تصدير البيانات إلى:\n{file_path}",
                fg="green"
            )
        except Exception as e:
            status_export.config(
                text=f"❌ خطأ أثناء التصدير:\n{str(e)}",
                fg="red"
            )

    export_button = tk.Button(stats_window, text="💾 تصدير الإحصائيات إلى Excel", font=button_font, bg=button_color, fg="white", command=export_stats)
    export_button.pack(pady=(5, 10))

# ---------- Theme & Fonts ----------

bg_color = "#eaeaea"
button_color = "#2b5797"
title_font = ("Helvetica", 16, "bold")
body_font = ("Helvetica", 12)
button_font = ("Helvetica", 12, "bold")

# ---------- Init ----------

init_db()
# insert_fake_data()  # Uncomment if needed

root = tk.Tk()
root.title("برنامج تسجيل الوجبات")
root.geometry("800x700")
root.configure(bg=bg_color)
root.resizable(False, False)


def add_placeholder(entry, placeholder_text, color='grey'):
    def on_focus_in(event):
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_focus_out(event):
        if not entry.get():
            entry.insert(0, placeholder_text)
            entry.config(fg=color)

    entry.insert(0, placeholder_text)
    entry.config(fg=color)
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)


#Main button
def create_modern_button(master, text, command, bg="#2b5797", fg="#2b5797", hover_bg="#1e3d73"):
    def on_enter(e):
        btn['background'] = hover_bg

    def on_leave(e):
        btn['background'] = bg

    btn = tk.Button(master,
                    text=text,
                    font=("Helvetica", 12, "bold"),
                    bg=bg,
                    fg=fg,
                    activeforeground=fg,
                    activebackground=hover_bg,
                    bd=0,
                    padx=20,
                    pady=10,
                    cursor="hand2")

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.configure(command=command)
    return btn


# ---------- Logo ----------
logo_path = os.path.join("assets", "logo.png")
if os.path.exists(logo_path):
    img = Image.open(logo_path)
    resized_img = img.resize((300, 85))  # Set desired width x height here
    logo_img = ImageTk.PhotoImage(resized_img)
    tk.Label(root, image=logo_img, bg=bg_color).pack(pady=(10, 5))

# ---------- Title ----------
tk.Label(root, text="معهد التدريب النفطي / بيجي", font=title_font, bg=bg_color, fg="#333").pack(pady=(0, 10))

tk.Label(root, text="برنامج تسجيل استلام الوجبات", font=title_font, bg=bg_color, fg="#333").pack(pady=(0, 10))

# --------- Input Section with Label ---------
input_wrapper = tk.Frame(root, bg=bg_color)
input_wrapper.pack(pady=(10, 5))

# Label above input field
input_label = tk.Label(input_wrapper, text="رقم التعريفي للموظف",fg="#333", font=("Helvetica", 10, "bold"), bg=bg_color, anchor='e')
input_label.pack(anchor='e', padx=50)

# Simulated rounded input field container
rounded_frame = tk.Frame(input_wrapper, bg="#eaeaea", bd=0)
rounded_frame.pack(padx=10, pady=5)

entry_container = tk.Frame(rounded_frame, bg="#eaeaea")
entry_container.pack(ipadx=10, ipady=6)

# Optional icon (📷 or PNG)
qr_icon_path = os.path.join("assets", "qr_icon.png")
if os.path.exists(qr_icon_path):
    qr_img = Image.open(qr_icon_path).resize((24, 24))
    qr_icon = ImageTk.PhotoImage(qr_img)
    icon_label = tk.Label(entry_container, image=qr_icon, bg="#eaeaea")
else:
    icon_label = tk.Label(entry_container, text="📷", font=("Helvetica", 14), bg="#eaeaea")

icon_label.pack(side=tk.RIGHT, padx=(10, 0))

# Entry field itself
entry_customer_id = tk.Entry(entry_container,
                             font=("Helvetica", 14),
                             bd=0,
                             bg="#eaeaea",
                             fg="#333",
                             justify='right',
                             insertbackground="#333",
                             width=30)
entry_customer_id.pack(side=tk.RIGHT, ipady=6, padx=(0, 5))
entry_customer_id.focus()


log_button = create_modern_button(root, "📝 تسجيل الوجبة", log_meal, bg="#0078D7", hover_bg="#005a9e")
log_button.pack(pady=8)

stats_button = create_modern_button(root, "📊 عرض الإحصائيات", show_stats, bg="#4CAF50", hover_bg="#388E3C")
stats_button.pack(pady=5)

status_label = tk.Label(root, text="", font=body_font, bg=bg_color)
status_label.pack(pady=5)

# ---------- Table ----------
style = ttk.Style()
style.theme_use("default")



table = ttk.Treeview(root, columns=("ID", "Time"), show='headings', height=10)
table.heading("ID", text="رقم الموظف")

table.heading("Time", text="الوقت والتاريخ")
table.pack(pady=15, padx=15, fill=tk.BOTH)




# ---------- Run ----------
root.mainloop()