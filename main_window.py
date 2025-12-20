import sqlite3
from load_XAML import load_xaml
from System.Windows import WindowState
from message_box import show_message

class MainWindow:
    def __init__(self):
        self.window = load_xaml("MainWindow.xaml")
        self.set_events()

    def set_events(self):
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_minimized = self.window.FindName("BtnMinimized")
        self.btn_maximized = self.window.FindName("BtnMaximized")
        self.rbtn_warehouse = self.window.FindName("RBtnWarehouseRadio")
        self.rbtn_order = self.window.FindName("RBtnOrderRadio")
        self.btn_logout = self.window.FindName("BtnLogout")
        self.btn_close.Click += lambda s, e: self.window.Close()
        self.btn_minimized.Click += self.minimized_window
        self.btn_maximized.Click += self.maximized_window
        self.btn_logout.Click += self.logout

    def maximized_window(self, sender, e):
        if self.window.WindowState == WindowState.Maximized:
            self.window.WindowState = WindowState.Normal
        else:
            self.window.WindowState = WindowState.Maximized

    def minimized_window(self, sender, e):
        self.window.WindowState = WindowState.Minimized

    def logout(self, sender, e):
        if show_message("Предупреждение","Вы действительно хотите выйти?","warning","yesno") == "yes":
            from login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.window.Close()

    def show(self):
        self.window.Show()