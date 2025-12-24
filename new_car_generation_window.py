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

class NewCarGenerationWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewCarGenerationWindow.xaml")
        self.user_id = user_id
        self.set_events()
        self.load_car_brand() 

    def set_events(self):
        self.cmb_car_brand = self.window.FindName("CarBrandComboBox")
        self.cmb_car_model = self.window.FindName("CarModelComboBox")
        self.txt_title = self.window.FindName("CarGenerationTextBox")
        self.border = self.window.FindName("TitleBar")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.cmb_car_brand.SelectionChanged += self.on_brand_changed
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_save.Click += self.save_generation
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

    def on_brand_changed(self, s, e):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM CarModel WHERE brand_id = ? ORDER BY title", (self.cmb_car_brand.SelectedItem.Id,))
        self.cmb_car_model.Items.Clear()
        for row in cur.fetchall():
            self.cmb_car_model.Items.Add(ComboItem(row[0], row[1]))

    def save_generation(self, sender, e):
        errors = False
        if self.txt_title.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return

        model_id = self.cmb_car_model.SelectedItem.Id
        if model_id is None:
            show_message("Ошибка", "Выберите модель", "error", "ok")
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("SELECT id FROM CarGeneration WHERE model_id = ? AND title = ?",(model_id, self.txt_title.Text)).fetchall()
        if temp:
            show_message("Ошибка", "Данная конфигурация уже существует", "error", "ok")
            return
        
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("INSERT INTO CarGeneration (title, model_id) VALUES (?, ?)", (self.txt_title.Text, model_id))
            conn.commit()
            show_message("Успех", f"Поколение {self.txt_title.Text} успешно сохранено!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()