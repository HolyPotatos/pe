import sqlite3
from load_XAML import load_xaml
from System.Windows.Input import MouseButtonState
from message_box import show_message


class NewCarBrandWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewCarBrandWindow.xaml")
        self.user_id = user_id
        self.set_events()


    def set_events(self):
        self.border = self.window.FindName("TitleBar")
        self.txt_title = self.window.FindName("CarBrandTextBox")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.border.MouseLeftButtonDown +=  self.drag_window
        self.btn_save.Click += self.save_brand
        self.btn_cancel.Click += lambda s, e: self.window.Close()
        self.btn_close.Click += lambda s, e: self.window.Close()

    def show(self):
        self.window.ShowDialog() 

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()    

    def save_brand(self, sender, e):
        errors = False
        if self.txt_title.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("SELECT id FROM CarBrand WHERE title = ?",(self.txt_title.Text,)).fetchall()
        if temp:
            show_message("Ошибка", "Такая марка уже существует", "error", "ok")
            return
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("INSERT INTO CarBrand (title) VALUES (?)", (self.txt_title.Text,))
            conn.commit()
            show_message("Успех", f"Марка {self.txt_title.Text} успешно добавлена!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()