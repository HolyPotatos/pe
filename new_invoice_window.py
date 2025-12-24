import sqlite3
from datetime import datetime
from load_XAML import load_xaml
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Input import MouseButtonState
from System import Object
from Microsoft.Win32 import OpenFileDialog
from message_box import show_message
import models



class InvoiceItem:
    def __init__(self, part, count):
        self.PartID = part.Id
        self.Sku = part.Sku
        self.Title = part.Title
        self.Count = count

class ComboItem:
    def __init__(self, id, title):
        self.Id = id
        self.Title = title
    def __str__(self):
        return self.Title

class NewInvoiceWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewInvoiceWindow.xaml")
        self.user_id = user_id
        self.pdf_file = None
        self.invoice_items = ObservableCollection[Object]() 
        self.set_events()
        self.load_initial_data()
        self.update_data(None)


    def set_events(self):
        self.cmb_supplier = self.window.FindName("ComboSupplier")
        self.border = self.window.FindName("TitleBar")
        self.txt_search = self.window.FindName("TxtSearchPart")
        self.grid_search = self.window.FindName("GridSearchParts")
        self.txt_qty = self.window.FindName("TxtQuantity")
        self.btn_add = self.window.FindName("BtnAdd")
        self.grid_invoice = self.window.FindName("GridInvoice")
        self.btn_remove = self.window.FindName("BtnRemove")
        self.btn_save = self.window.FindName("BtnSaveInvoice")
        self.btn_add_file = self.window.FindName("BtnAddFile")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.btn_new_supplier = self.window.FindName("BtnNewSupplier")
        self.btn_add_file = self.window.FindName("BtnAddFile")        
        self.border.MouseLeftButtonDown += self.drag_window
        self.grid_invoice.ItemsSource = self.invoice_items
        self.txt_search.TextChanged += self.on_search_changed
        self.btn_add.Click += self.on_add_to_invoice
        self.btn_remove.Click += self.on_remove_from_invoice
        self.btn_save.Click += self.on_save_invoice
        self.btn_add_file.Click += self.on_add_file
        self.btn_new_supplier.Click += self.on_new_supplier
        self.btn_cancel.Click += lambda s, e: self.window.Close()
        self.btn_close.Click += lambda s, e: self.window.Close()

    def show(self):
        self.window.ShowDialog() 

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()    

    def load_initial_data(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM Supplier")
        for row in cur.fetchall():
            self.cmb_supplier.Items.Add(ComboItem(row[0], row[1]))
        conn.close()
        self.cmb_supplier.SelectedIndex = 0

    def update_data(self, filter):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        if filter is None:
            cur.execute("""
            SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
            FROM AutoPart ap
            JOIN BrandPart bp ON ap.brand_id = bp.id
            """)
        else:
            cur.execute("""
            SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
            FROM AutoPart ap
            JOIN BrandPart bp ON ap.brand_id = bp.id
            WHERE ap.title LIKE ? OR ap.sku LIKE ?
            """,(f"%{filter}%", f"%{filter}%"))
        rows = cur.fetchall()
        self.parts = List[Object]()
        for row in rows:
            self.parts.Add(models.AutoPart(*row))
            
        self.grid_search.ItemsSource = self.parts
        conn.close()

    def on_search_changed(self, sender, e):
        text = self.txt_search.Text
        if len(text) < 1:
            self.update_data(None) 
            return
        self.update_data(text)
        

    def on_add_to_invoice(self, sender, e):
        selected_part = self.grid_search.SelectedItem
        if not selected_part:
            show_message("Ошибка", "Выберите запчасть из списка", "error", "ok")
            return
            
        try:
            qty = int(self.txt_qty.Text)
            if qty <= 0: raise ValueError
        except:
            show_message("Ошибка", "Введите корректное количество", "error", "ok")
            return

        for item in self.invoice_items:
            if item.PartID == selected_part.Id:
                item.Count += qty
                self.grid_invoice.Items.Refresh()
                return

        self.invoice_items.Add(InvoiceItem(selected_part, qty))

    def on_remove_from_invoice(self, sender, e):
        selected = self.grid_invoice.SelectedItem
        if selected:
            self.invoice_items.Remove(selected)

    def on_save_invoice(self, sender, e):
        if self.invoice_items.Count == 0:
            show_message("Ошибка", "Вы не добавили ни одной запчасти в приход", "error", "ok")
            return
        if self.pdf_file is None:
            if show_message("Предупреждение", "Вы не добавили файл накладной!\nДобавить приход без накладной?", "warning", "yesno") == "no":
                return
        
        supplier_id = self.cmb_supplier.SelectedItem.Id
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        
        try:
            cur.execute("BEGIN TRANSACTION")
            current_date = datetime.now().strftime("%Y-%m-%d")
            cur.execute("""
                INSERT INTO Invoice (invoice_date, file, supplier_id)
                VALUES (?, ?, ?)""", 
                (current_date, self.pdf_file, supplier_id))
            
            invoice_id = cur.lastrowid
            
            for item in self.invoice_items:
                cur.execute("""
                    INSERT INTO InvoiceParts (count, invoice_id, part_id)
                    VALUES (?, ?, ?)""", 
                    (item.Count, invoice_id, item.PartID))
                cur.execute("UPDATE AutoPart SET stock = stock + ? WHERE id = ?", (item.Count, item.PartID))
            
            conn.commit()
            show_message("Успех", f"Приход №{invoice_id} успешно создан!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()

    def on_add_file(self, s, e):
        dialog = OpenFileDialog()
        dialog.Filter = "PDF Files (*.pdf)|*.pdf"
        dialog.Title = "Выберите PDF-файл накладной"
        if not dialog.ShowDialog():
            return 
        with open(dialog.FileName, 'rb') as file:
            self.pdf_file = file.read()
        show_message("Уведомление","Файл успешно загружен","info","ok")

    def on_new_supplier(self, s, e):
        from new_supplier_window import NewSupplierWindow
        temp = NewSupplierWindow(self.user_id)
        temp.show()
        self.load_initial_data()

        