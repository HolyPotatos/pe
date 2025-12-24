import sqlite3
from load_XAML import load_xaml
from System.Windows.Input import MouseButtonState
from security import password_check
from message_box import show_message



class LoginWindow:
    def __init__(self):
        self.window = load_xaml("LoginWindow.xaml")
        self.set_events()

    def set_events(self):
        btn_close = self.window.FindName("BtnClose")
        self.login_box = self.window.FindName("loginBox")
        self.pass_box = self.window.FindName("passBox")
        btn_login = self.window.FindName("loginBtn")
        btn_close.Click += lambda s, e: self.window.Close()
        self.window.MouseLeftButtonDown += self.drag_window
        self.pass_box.PasswordChanged += self.on_password_changed
        btn_login.Click += self.on_login_click

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()

    def on_password_changed(self, sender, e):
        if self.pass_box.Password:
            self.pass_box.Tag = ""
        else:
            self.pass_box.Tag = "Пароль"

    def show(self):
        self.window.Show()

    def on_login_click(self, sender, e):
        auth_login = self.login_box.Text
        auth_password = self.pass_box.Password
        if auth_login == "" or auth_password == "":
            show_message("Ошибка","Необходимо заполнить все поля.","error","ok")
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT user_id, password_hash, salt, is_active FROM UserAuthData WHERE login = ?", (auth_login,))
        data = cur.fetchone()
        conn.close()
        if data == None:
            show_message("Ошибка","Такого аккаунта нет!","error","ok")
            return
        id, stored_hash, stored_salt, is_active = data
        if password_check(stored_hash, stored_salt, auth_password) and is_active == 1:
            from main_window import MainWindow
            self.main_window = MainWindow(id)
            self.main_window.show()
            self.window.Close()
        else:
            show_message("Ошибка","Такого аккаунта нет!","error","ok")
            return