import sqlite3
from load_XAML import load_xaml
from System.Windows.Input import MouseButtonState
from message_box import show_message
import security


class ComboItem:
    def __init__(self, id, title):
        self.Id = id
        self.Title = title
    def __str__(self):
        return self.Title

class NewUserWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewUserWindow.xaml")
        self.user_id = user_id
        self.set_events()
        self.load_user_role()


    def set_events(self):
        self.cmb_role = self.window.FindName("RoleComboBox")
        self.border = self.window.FindName("TitleBar")
        self.txt_name = self.window.FindName("NameTextBox")
        self.txt_surname = self.window.FindName("SurnameTextBox")
        self.txt_patronymic = self.window.FindName("PatronymicTextBox")
        self.txt_email = self.window.FindName("EMailTextBox")
        self.txt_phone = self.window.FindName("PhoneTextBox")
        self.txt_login = self.window.FindName("LoginTextBox")
        self.txt_password = self.window.FindName("PasswordTextBox")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_save.Click += self.save_user
        self.btn_cancel.Click += lambda s, e: self.window.Close()
        self.btn_close.Click += lambda s, e: self.window.Close()

    def show(self):
        self.window.ShowDialog() 

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()    

    def load_user_role(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM UserRole")
        for row in cur.fetchall():
            self.cmb_role.Items.Add(ComboItem(row[0], row[1]))
        conn.close()
        self.cmb_role.SelectedIndex = 0

    def save_user(self, sender, e):
        errors = False
        if self.txt_email.Text == "": errors = True
        if self.txt_login.Text == "": errors = True
        if self.txt_name.Text == "": errors = True
        if self.txt_password.Text == "": errors = True
        if self.txt_patronymic.Text == "": errors = True
        if self.txt_phone.Text == "": errors = True
        if self.txt_surname.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return
        
        role_id = self.cmb_role.SelectedItem.Id
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("""SELECT u.id FROM User u
                    JOIN UserAuthData ud ON ud.user_id = u.id WHERE u.email = ?
                    OR u.phone_number = ? or ud.login = ?""",
                    (self.txt_email.Text, self.txt_phone.Text, self.txt_login.Text)).fetchall()
        if temp:
            show_message("Ошибка", "Пользователь с такими данными уже существует", "error", "ok")
            return
        
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("""
                INSERT INTO User (name, surname, patronymic, email, phone_number, role_id)
                VALUES (?, ?, ?, ?, ?, ?)""", 
                (self.txt_name.Text, self.txt_surname.Text, self.txt_patronymic.Text, self.txt_email.Text, self.txt_phone.Text, role_id))
            
            user_id = cur.lastrowid
            password_hash, salt = security.password_hash(self.txt_password.Text)
            cur.execute("""INSERT INTO UserAuthData (user_id, login, password_hash, salt)
            VALUES (?, ?, ?, ?)""", (user_id, self.txt_login.Text, password_hash, salt))
            conn.commit()
            show_message("Успех", f"Пользователь №{user_id} успешно создан!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()