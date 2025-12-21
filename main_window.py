import sqlite3
import models
from load_XAML import load_xaml
from System.Windows import WindowState
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class MainWindow:
    def __init__(self):
        self.window = load_xaml("MainWindow.xaml")
        self.set_main_events()
        self.order_content = load_xaml("OrdersView.xaml")
        self.set_order_events()
        self.warehouse_content = load_xaml("WarehouseView.xaml")
        self.set_warehouse_events()
        self.navigate(self.order_content)
        self.update_data()

    def set_order_events(self):
        self.order_datagrid = self.order_content.FindName("OrderDataGrid")

    def set_warehouse_events(self):
        pass

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
    
    def update_data(self):
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
                    """)
        self.orders = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.orders.Add(models.Orders(*i[:12]))
        self.order_datagrid.ItemsSource = self.orders

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