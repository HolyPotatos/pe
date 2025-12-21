import sqlite3
import models
from datetime import datetime
from load_XAML import load_xaml
from System.Windows import WindowState
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class MainWindow:
    def __init__(self, user_id):
        self.window = load_xaml("MainWindow.xaml")
        self.set_main_events()
        self.order_content = load_xaml("OrdersView.xaml")
        self.set_order_events()
        self.warehouse_content = load_xaml("WarehouseView.xaml")
        self.set_warehouse_events()
        self.navigate(self.order_content)
        self.update_data_order()
    
    #Главное окно

    def set_main_events(self):
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_minimized = self.window.FindName("BtnMinimized")
        self.btn_maximized = self.window.FindName("BtnMaximized")
        self.rbtn_warehouse = self.window.FindName("RBtnWarehouseRadio")
        self.rbtn_order = self.window.FindName("RBtnOrderRadio")
        self.btn_logout = self.window.FindName("BtnLogout")
        self.content_control = self.window.FindName("MainContentControl")
        self.btn_close.Click += lambda s, e: self.window.Close()
        self.btn_minimized.Click += self.minimized_window
        self.btn_maximized.Click += self.maximized_window
        self.btn_logout.Click += self.logout
        self.rbtn_order.Click += lambda s, e: self.navigate(self.order_content)
        self.rbtn_warehouse.Click += lambda s, e: self.navigate(self.warehouse_content)
    
    def maximized_window(self, sender, e):
        if self.window.WindowState == WindowState.Maximized:
            self.window.WindowState = WindowState.Normal
        else:
            self.window.WindowState = WindowState.Maximized

    def minimized_window(self, sender, e):
        self.window.WindowState = WindowState.Minimized
    
    def navigate(self, view):
        self.content_control.Content = view

    def logout(self, sender, e):
        if show_message("Предупреждение","Вы действительно хотите выйти?","warning","yesno") == "yes":
            from login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.window.Close()

    def show(self):
        self.window.Show()
    
    #Страница заказов

    def set_order_events(self):
        self.selected_order_id = -1
        self.order_datagrid = self.order_content.FindName("OrderDataGrid")
        self.order_part_datagrid = self.order_content.FindName("OrderPartsDataGrid")
        self.btn_new_order = self.order_content.FindName("OrderPartsDataGrid")
        self.btn_order_cancel = self.order_content.FindName("BtnOrderCansel")
        self.btn_order_history = self.order_content.FindName("BtnOrderHistory")
        self.btn_order_more = self.order_content.FindName("BtnOrderMore")
        self.tb_search = self.order_content.FindName("SearchBar")
        self.tb_search.TextChanged += lambda s, e: self.update_data_order()
        self.order_datagrid.SelectionChanged += self.on_order_selected
        self.btn_order_cancel.Click += self.on_order_cansel_click
        self.btn_order_history.Click += self.on_history_click

    def on_order_selected(self, s, e):
        grid = s 
        selected_item = grid.SelectedItem
        if selected_item is None:
            self.btn_order_cancel.IsEnabled = False
            self.btn_order_history.IsEnabled = False
            self.btn_order_more.IsEnabled = False
        else:
            self.btn_order_cancel.IsEnabled = True
            self.btn_order_history.IsEnabled = True
            self.btn_order_more.IsEnabled = True
            self.update_data_order_parts(selected_item.ID)
            self.selected_order_id = selected_item.ID

    def update_data_order_parts(self, order_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT op.part_id, p.sku, p.title, op.order_id, op.count, op.unit_retail_price, op.unit_purchase_price
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
        cur.execute("""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    o.client_id, dt.title, ot.title, os.title, pt.title, ps.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderType ot ON ot.id = o.order_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    JOIN PaymentStatus ps ON ps.id = o.payment_status_id
                    WHERE o.delivery_address LIKE ?
                    """, (f"%{self.tb_search.Text}%",))
        self.orders = List[Object]()
        print(self.tb_search.Text.lower())
        rows = cur.fetchall()
        for i in rows:
            self.orders.Add(models.Orders(*i[:12]))
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
            cur.execute("INSERT INTO OrderStatusHistory (date_time, old_value_id, new_value_id, order_id) VALUES (?,?,?,?) ", (current_date, old_value_id, 5, self.selected_order_id))
            cur.execute("UPDATE Orders SET order_status_id = 5 WHERE id = ?", (self.selected_order_id,))
            conn.commit()
            conn.close
            self.update_data_order()
        else:
            return
        
    def on_history_click(self, s, e):
        from order_history import OrderHistory
        ohis = OrderHistory(self.selected_order_id)
        ohis.show()

    def on_search_changed(self, s, e):
        self.update_data_order

    #Страница склада

    def set_warehouse_events(self):
        pass
