import sqlite3
from System.Windows import WindowState
from load_XAML import load_xaml
from message_box import show_message
from warehouse_view import WarehouseView
from orders_view import OrdersView
from user_view import UserView

class MainWindow:
    def __init__(self, user_id):
        self.window = load_xaml("MainWindow.xaml")
        self.set_events()
        self.order_content = OrdersView(user_id)
        self.user_content = UserView(user_id)
        self.warehouse_content = WarehouseView(user_id)
        self.navigate(self.order_content.get_view())
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT role_id FROM User WHERE id = ?",(user_id,))
        self.user_role = int(cur.fetchone()[0])
        conn.close()
        print(self.user_role)
        self.user_id = user_id

    def set_events(self):
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_minimized = self.window.FindName("BtnMinimized")
        self.btn_maximized = self.window.FindName("BtnMaximized")
        self.rbtn_warehouse = self.window.FindName("RBtnWarehouseRadio")
        self.rbtn_order = self.window.FindName("RBtnOrderRadio")
        self.rbtn_user = self.window.FindName("RBtnUserRadio")
        self.btn_logout = self.window.FindName("BtnLogout")
        self.content_control = self.window.FindName("MainContentControl")
        self.btn_close.Click += lambda s, e: self.window.Close()
        self.btn_minimized.Click += self.minimized_window
        self.btn_maximized.Click += self.maximized_window
        self.btn_logout.Click += self.logout
        self.rbtn_user.Click += lambda s, e: self.navigate(self.user_content.get_view())
        self.rbtn_order.Click += lambda s, e: self.navigate(self.order_content.get_view())
        self.rbtn_warehouse.Click += lambda s, e: self.navigate(self.warehouse_content.get_view())


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
    