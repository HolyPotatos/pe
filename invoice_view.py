import sqlite3
import models
from load_XAML import load_xaml
from System.Collections.Generic import List
from System import Object
from Microsoft.Win32 import SaveFileDialog
from message_box import show_message


class InvoiceView:
    def __init__(self, user_id):
        self.view = load_xaml("InvoiceView.xaml")
        self.set_events()
        self.user_id = user_id

    def set_events(self):
        self.selected_invoice_id = -1
        self.invoice_datagrid = self.view.FindName("InvoiceDataGrid")
        self.invoice_part_datagrid = self.view.FindName("InvoicePartsDataGrid")
        self.btn_new_invoice = self.view.FindName("BtnNewInvoice")
        self.btn_show_pdf = self.view.FindName("BtnShowPDF")
        self.invoice_datagrid.SelectionChanged += self.on_invoice_selected
        self.btn_show_pdf.Click += self.on_show_pdf
        self.btn_new_invoice.Click += self.open_new_invoice_window
        self.update_data_invoice()

    def get_view(self):
        return self.view

    def open_new_invoice_window(self, sender, e):
        from new_invoice_window import NewInvoiceWindow   
        nw = NewInvoiceWindow(self.user_id)
        nw.show()
        self.update_data_invoice()

    def on_invoice_selected(self, s, e):
        grid = s 
        selected_item = grid.SelectedItem
        if selected_item is None:
            self.btn_show_pdf.IsEnabled = False
        else:
            self.btn_show_pdf.IsEnabled = True
            self.update_data_invoice_parts(selected_item.ID)
            self.selected_invoice_id = selected_item.ID

    def update_data_invoice_parts(self, invoice_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT ip.part_id, p.sku, p.title, ip.count
                    FROM InvoiceParts ip
                    JOIN AutoPart p ON ip.part_id = p.id
                    WHERE ip.invoice_id = ?
                    """,(invoice_id,))
        self.invoice_parts = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.invoice_parts.Add(models.InvoiceParts(*i))
        self.invoice_part_datagrid.ItemsSource = self.invoice_parts
        conn.close()

    def update_data_invoice(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT i.id, i.invoice_date, s.title FROM Invoice i
                    JOIN Supplier s ON s.id = i.supplier_id
                    ORDER BY i.invoice_date DESC""")
        self.invoice = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.invoice.Add(models.Invoice(*i))
        self.invoice_datagrid.ItemsSource = self.invoice
        conn.close()
        
    def on_show_pdf(self, s, e):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        invoice_id, blob_data = cur.execute("SELECT id, file FROM Invoice WHERE id = ?",(self.selected_invoice_id,)).fetchone()
        if blob_data is None:
            show_message("Ошибка!","В данном приходе нет файла с накладной.","error","ok")
            return
        dialog = SaveFileDialog()
        dialog.Filter = "PDF Files (*.pdf)|*.pdf"
        dialog.FileName = f"invoice_{invoice_id}"
        dialog.Title = "Выберите место для сохранения файла"
        if dialog.ShowDialog():
            try:
                save_path = dialog.FileName
                with open(save_path, 'wb') as f:
                    f.write(blob_data)
                show_message("Уведомление","Файл успешно сохранен","info","ok")
            except Exception as e:
                show_message("Ошибка!",str(e),"error","ok")
            