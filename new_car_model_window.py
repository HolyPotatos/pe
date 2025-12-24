import sqlite3
from load_XAML import load_xaml
from System.Windows.Input import MouseButtonState
from message_box import show_message


class ComboItem:
    def __init__(self, id, title):
        self.Id = id
        self.Title = title
    def __str__(self):
        return self.Title

class NewCarModelWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewCarModelWindow.xaml")
        self.user_id = user_id
        self.set_events()
        self.load_car_brand() 

    def set_events(self):
        self.cmb_car_brand = self.window.FindName("CarBrandComboBox")
        self.txt_model = self.window.FindName("CarModelTextBox")
        self.border = self.window.FindName("TitleBar")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_save.Click += self.save_car_model
        self.btn_cancel.Click += lambda s, e: self.window.Close()
        self.btn_close.Click += lambda s, e: self.window.Close()

    def show(self):
        self.window.ShowDialog() 

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()    

    def load_car_brand(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM CarBrand ORDER BY title")
        for row in cur.fetchall():
            self.cmb_car_brand.Items.Add(ComboItem(row[0], row[1]))
        conn.close()
        self.cmb_car_brand.SelectedIndex = 0

    def save_car_model(self, sender, e):
        errors = False
        if self.txt_model.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return

        brand_id = self.cmb_car_brand.SelectedItem.Id
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("SELECT id FROM CarModel WHERE brand_id = ? AND title = ?",(brand_id, self.txt_model.Text)).fetchall()
        if temp:
            show_message("Ошибка", "Данная модель уже существует", "error", "ok")
            return
        
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("INSERT INTO CarModel (title, brand_id) VALUES (?, ?)", (self.txt_model.Text, brand_id))
            conn.commit()
            show_message("Успех", f"Модель {self.txt_model.Text} успешно сохранена!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()