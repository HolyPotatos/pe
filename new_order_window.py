import sqlite3
from datetime import datetime
from load_XAML import load_xaml
from System.Collections.Generic import List
from System.Collections.ObjectModel import ObservableCollection
from System.Windows.Input import MouseButtonState
from System import Object
from message_box import show_message
import models



class CartItem:
    def __init__(self, part, count):
        self.PartID = part.Id
        self.Sku = part.Sku
        self.Title = part.Title
        self.RetailPrice = part.RetailPrice
        self.Count = count
    
    @property
    def TotalPrice(self):
        return self.RetailPrice * self.Count

class ComboItem:
    def __init__(self, id, title):
        self.Id = id
        self.Title = title
    def __str__(self):
        return self.Title

class NewOrderWindow:
    def __init__(self, seller_id):
        self.window = load_xaml("NewOrderWindow.xaml")
        self.seller_id = seller_id
        self.cart_items = ObservableCollection[Object]() 
        self.set_events()
        self.load_initial_data()
        self.update_data(None)


    def set_events(self):
        self.cmb_delivery = self.window.FindName("ComboDelivery")
        self.cmb_payment = self.window.FindName("ComboPayment")
        self.txt_address = self.window.FindName("TxtAddress")
        self.border = self.window.FindName("TitleBar")
        self.txt_search = self.window.FindName("TxtSearchPart")
        self.grid_search = self.window.FindName("GridSearchParts")
        self.txt_qty = self.window.FindName("TxtQuantity")
        self.btn_add = self.window.FindName("BtnAdd")
        self.grid_cart = self.window.FindName("GridCart")
        self.btn_remove = self.window.FindName("BtnRemove")
        self.txt_total = self.window.FindName("TxtTotalSum")
        self.btn_save = self.window.FindName("BtnSaveOrder")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.border.MouseLeftButtonDown += self.drag_window
        self.grid_cart.ItemsSource = self.cart_items
        self.txt_search.TextChanged += self.on_search_changed
        self.btn_add.Click += self.on_add_to_cart
        self.btn_remove.Click += self.on_remove_from_cart
        self.btn_save.Click += self.on_save_order
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
        cur.execute("SELECT id, title FROM DeliveryType")
        for row in cur.fetchall():
            self.cmb_delivery.Items.Add(ComboItem(row[0], row[1]))
        cur.execute("SELECT id, title FROM PaymentType")
        for row in cur.fetchall():
            self.cmb_payment.Items.Add(ComboItem(row[0], row[1]))
        conn.close()
        
        self.cmb_delivery.SelectedIndex = 0
        self.cmb_payment.SelectedIndex = 0

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
        

    def on_add_to_cart(self, sender, e):
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

        if qty > selected_part.Stock:
            show_message("Внимание", f"На складе всего {selected_part.Stock} шт.", "warning", "ok")
            return

        for item in self.cart_items:
            if item.PartID == selected_part.Id:
                if item.Count + qty > selected_part.Stock:
                    show_message("Внимание", f"На складе всего {selected_part.Stock} шт.", "warning", "ok")
                    return
                item.Count += qty
                self.grid_cart.Items.Refresh()
                self.recalculate_total()
                return

        self.cart_items.Add(CartItem(selected_part, qty))
        self.recalculate_total()

    def on_remove_from_cart(self, sender, e):
        selected = self.grid_cart.SelectedItem
        if selected:
            self.cart_items.Remove(selected)
            self.recalculate_total()

    def recalculate_total(self):
        total = sum([item.TotalPrice for item in self.cart_items])
        self.txt_total.Text = f"{total:,.2f} ₽"

    def on_save_order(self, sender, e):
        if self.cart_items.Count == 0:
            show_message("Ошибка", "Корзина пуста", "error", "ok")
            return
        
        delivery_id = self.cmb_delivery.SelectedItem.Id
        payment_id = self.cmb_payment.SelectedItem.Id
        if delivery_id == 1:
            address = None
        else:
            address = self.txt_address.Text
        
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        
        try:
            if delivery_id == 1:
                order_status = 4
            else:
                order_status = 1
            cur.execute("BEGIN TRANSACTION")
            current_date = datetime.now().strftime("%Y-%m-%d")
            cur.execute("""
                INSERT INTO Orders (date, delivery_address, seller_id, storekeeper_id,  
                delivery_type_id, order_status_id, payment_type_id)
                VALUES (?, ?, ?, NULL, ?, ?, ?)""", 
                (current_date, address, self.seller_id, delivery_id, order_status, payment_id))
            
            order_id = cur.lastrowid
            
            for item in self.cart_items:
                cur.execute("""
                    INSERT INTO OrderParts (part_id, order_id, count, unit_retail_price)
                    VALUES (?, ?, ?, ?)""", 
                    (item.PartID, order_id, item.Count, item.RetailPrice))
                cur.execute("UPDATE AutoPart SET stock = stock - ? WHERE id = ?", (item.Count, item.PartID))
            
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            old_value_id = None
            cur.execute("INSERT INTO OrderStatusHistory (date_time, old_value_id, new_value_id, order_id) VALUES (?,?,?,?) ", (current_date, old_value_id, order_status, order_id))
            conn.commit()
            show_message("Успех", f"Заказ №{order_id} успешно создан!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()