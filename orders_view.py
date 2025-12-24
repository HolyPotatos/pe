import sqlite3
import models
from datetime import datetime
from load_XAML import load_xaml
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class OrdersView:
    def __init__(self, user_id):
        self.view = load_xaml("OrdersView.xaml")
        self.set_events()
        self.user_id = user_id

    def set_events(self):
        self.selected_order_id = -1
        self.order_datagrid = self.view.FindName("OrderDataGrid")
        self.order_part_datagrid = self.view.FindName("OrderPartsDataGrid")
        self.btn_new_order = self.view.FindName("BtnNewOrder")
        self.btn_order_cancel = self.view.FindName("BtnOrderCansel")
        self.btn_order_history = self.view.FindName("BtnOrderHistory")
        self.tb_search = self.view.FindName("SearchBar")
        self.tb_search.TextChanged += lambda s, e: self.update_data_order()
        self.order_datagrid.SelectionChanged += self.on_order_selected
        self.btn_order_cancel.Click += self.on_order_cansel_click
        self.btn_order_history.Click += self.on_history_click
        self.btn_new_order.Click += self.open_new_order_window
        self.update_data_order()

    def get_view(self):
        return self.view

    def open_new_order_window(self, sender, e):
        from new_order_window import NewOrderWindow         
        nw = NewOrderWindow(self.user_id)
        nw.show()
        self.update_data_order()

    def on_order_selected(self, s, e):
        grid = s 
        selected_item = grid.SelectedItem
        if selected_item is None:
            self.btn_order_cancel.IsEnabled = False
            self.btn_order_history.IsEnabled = False
        else:
            self.btn_order_cancel.IsEnabled = True
            self.btn_order_history.IsEnabled = True
            self.update_data_order_parts(selected_item.ID)
            self.selected_order_id = selected_item.ID

    def update_data_order_parts(self, order_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT op.part_id, p.sku, p.title, op.order_id, op.count, op.unit_retail_price
                    FROM OrderParts op
                    JOIN AutoPart p ON op.part_id = p.id
                    WHERE op.order_id = ?
                    """,(order_id,))
        self.orders_parts = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.orders_parts.Add(models.OrderParts(*i[:7]))
        self.order_part_datagrid.ItemsSource = self.orders_parts
        conn.close()

    def update_data_order(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        if self.tb_search.Text != "":
            cur.execute("""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    WHERE o.delivery_address LIKE ?
                    ORDER BY o.date DESC, os.title ASC 
                    """, (f"%{self.tb_search.Text}%",))
        else:
            cur.execute("""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    ORDER BY o.date DESC, os.title ASC""")
            
        self.orders = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            temp = models.Orders(*i)
            if i[2] == None:
                temp.DeliveryAddress = "Самовывоз"
            self.orders.Add(temp)
        self.order_datagrid.ItemsSource = self.orders
        conn.close()
    
    def on_order_cansel_click(self, s, e):
        if show_message("Предупреждение","Вы уверены что хотите отменить заказ?","warning","yesno") == "yes":
            conn = sqlite3.connect("autoparts_shop.db")
            cur = conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            old_value_id = int(cur.execute("SELECT order_status_id FROM Orders WHERE id = ?", (self.selected_order_id,)).fetchone()[0])
            if old_value_id == 5:
                show_message("Ошибка","Заказ уже отменён","error","ok")
                return
            if old_value_id == 4:
                show_message("Ошибка","Заказ уже выполнен","error","ok")
                return
            cur.execute("INSERT INTO OrderStatusHistory (date_time, old_value_id, new_value_id, order_id) VALUES (?,?,?,?) ", (current_date, old_value_id, 5, self.selected_order_id))
            cur.execute("UPDATE Orders SET order_status_id = 5 WHERE id = ?", (self.selected_order_id,))
            parts = cur.execute("SELECT part_id, count FROM OrderParts WHERE order_id = ?",(self.selected_order_id,)).fetchall()
            for part in parts:
                cur.execute("UPDATE AutoPart SET stock = stock + ? WHERE id = ?", (part[1], part[0]))
            conn.commit()
            conn.close
            self.update_data_order()
        else:
            return
        
    def on_history_click(self, s, e):
        from order_history import OrderHistory
        ohis = OrderHistory(self.selected_order_id)
        ohis.show()