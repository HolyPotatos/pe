import sqlite3
import models
from datetime import datetime
from load_XAML import load_xaml
from System.Collections.Generic import List
from System.Windows import Visibility
from System import Object
from message_box import show_message


class OrdersView:
    def __init__(self, user_id, user_role):
        self.view = load_xaml("OrdersView.xaml")
        self.user_role = user_role
        self.user_id = user_id
        self.set_events()

    def set_events(self):
        self.selected_order_id = -1
        self.order_datagrid = self.view.FindName("OrderDataGrid")
        self.order_part_datagrid = self.view.FindName("OrderPartsDataGrid")
        self.btn_new_order = self.view.FindName("BtnNewOrder")
        self.btn_order_cancel = self.view.FindName("BtnOrderCansel")
        self.btn_order_history = self.view.FindName("BtnOrderHistory")
        self.btn_order_status_change = self.view.FindName("BtnOrderStatusChange")
        self.tb_search = self.view.FindName("SearchBar")
        self.status1 = self.view.FindName("status1")
        self.status2 = self.view.FindName("status2")
        self.status3 = self.view.FindName("status3")
        self.status4 = self.view.FindName("status4")
        self.status5 = self.view.FindName("status5")
        if self.user_role == 3:
            self.status4.Visibility = Visibility.Collapsed
            self.status5.Visibility = Visibility.Collapsed
            self.btn_new_order.Visibility = Visibility.Collapsed
            self.btn_order_cancel.Visibility = Visibility.Collapsed
        elif self.user_role == 2:
            self.btn_order_status_change.Visibility = Visibility.Collapsed
        self.status4.Click += lambda s, e: self.update_data_order()
        self.status5.Click += lambda s, e: self.update_data_order()
        self.status1.Click += lambda s, e: self.update_data_order()
        self.status2.Click += lambda s, e: self.update_data_order()
        self.status3.Click += lambda s, e: self.update_data_order()
        self.btn_order_status_change.Click += lambda s, e: self.update_status()
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
            if self.user_role == 3:
                self.btn_order_status_change.IsEnabled = False
        else:
            self.btn_order_cancel.IsEnabled = True
            self.btn_order_history.IsEnabled = True
            self.update_data_order_parts(selected_item.ID)
            self.selected_order_id = selected_item.ID
            if self.user_role == 3:
                os = self.order_datagrid.SelectedItem.OrderStatus
                self.btn_order_status_change.IsEnabled = True
                if os == "В обработке": self.btn_order_status_change.Content = "Заказ собран"
                if os == "Собран": self.btn_order_status_change.Content = "Закан в доставке"
                if os == "Передан в доставку": self.btn_order_status_change.Content = "Заказ доставлен"

    def update_status(self):
        if self.order_datagrid.SelectedItem.OrderStatus == "В обработке":
            message = "Вы подтверждаете что заказ собран и готов к отгрузке?"
        elif self.order_datagrid.SelectedItem.OrderStatus == "Собран":
            message = "Вы подтверждаете что заказ передан в доставку?"
        elif self.order_datagrid.SelectedItem.OrderStatus == "Передан в доставку":
            message = "Вы подтверждаете что покупатель получил товар?"
        if show_message("Предупреждение",message,"warning","yesno") == "yes":
            conn = sqlite3.connect("autoparts_shop.db")
            cur = conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            old_value_id = int(cur.execute("SELECT order_status_id FROM Orders WHERE id = ?", (self.selected_order_id,)).fetchone()[0])
            new_value_id = old_value_id + 1
            cur.execute("INSERT INTO OrderStatusHistory (date_time, old_value_id, new_value_id, order_id) VALUES (?,?,?,?) ", (current_date, old_value_id, new_value_id, self.selected_order_id))
            cur.execute("UPDATE Orders SET order_status_id = ? WHERE id = ?", (new_value_id, self.selected_order_id,))
            conn.commit()
            conn.close
            self.update_data_order()
        else:
            return

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
        filter_status = []
        if self.status1.IsChecked: filter_status.append("1")
        if self.status2.IsChecked: filter_status.append("2")
        if self.status3.IsChecked: filter_status.append("3")
        if self.user_role != 3:
            if self.status4.IsChecked: filter_status.append("4")
            if self.status5.IsChecked: filter_status.append("5")
        placeholders = ','.join('?' for _ in filter_status)
        if filter_status.count == 0:
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        if self.tb_search.Text != "":
            cur.execute(f"""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    WHERE o.delivery_address LIKE ? AND o.order_status_id IN ({placeholders})
                    ORDER BY o.date DESC, os.title ASC 
                    """, ([f"%{self.tb_search.Text}%"] + filter_status))
        else:
            cur.execute(f"""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    WHERE o.order_status_id IN ({placeholders})
                    ORDER BY o.date DESC, os.title ASC""",
                    filter_status)
            
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