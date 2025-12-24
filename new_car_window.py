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

class NewCarWindow:
    def __init__(self, user_id):
        self.window = load_xaml("NewCarWindow.xaml")
        self.user_id = user_id
        self.set_events()
        self.load_car_brand() 

    def set_events(self):
        self.cmb_car_brand = self.window.FindName("CarBrandComboBox")
        self.cmb_car_model = self.window.FindName("CarModelComboBox")
        self.cmb_car_generation = self.window.FindName("CarGenerationComboBox")
        self.txt_config = self.window.FindName("ConfigTextBox")
        self.border = self.window.FindName("TitleBar")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.btn_add_car_brand = self.window.FindName("BtnAddCarBrand")
        self.btn_add_car_model = self.window.FindName("BtnAddCarModel")
        self.btn_add_car_generation = self.window.FindName("BtnAddCarGeneration")
        self.cmb_car_brand.SelectionChanged += self.on_brand_changed
        self.cmb_car_model.SelectionChanged += self.on_model_changed
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_save.Click += self.save_car
        self.btn_add_car_brand.Click += self.new_car_brand_click
        self.btn_add_car_model.Click += self.new_car_model_click
        self.btn_add_car_generation.Click += self.new_car_generation_click
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
        self.cmb_car_brand.Items.Clear()
        for row in cur.fetchall():
            self.cmb_car_brand.Items.Add(ComboItem(row[0], row[1]))
        conn.close()
        self.cmb_car_brand.SelectedIndex = 0
    
    def new_car_brand_click(self, s, e):
        from new_car_brand_window import NewCarBrandWindow
        nbw = NewCarBrandWindow(self.user_id)
        nbw.show()
        self.cmb_car_model.Items.Clear()
        self.cmb_car_generation.Items.Clear()
        self.load_car_brand()

    def new_car_model_click(self, s, e):
        from new_car_model_window import NewCarModelWindow
        nbw = NewCarModelWindow(self.user_id)
        nbw.show()
        self.cmb_car_model.Items.Clear()
        self.cmb_car_generation.Items.Clear()
        self.load_car_brand()

    def new_car_generation_click(self, s, e):
        from new_car_generation_window import NewCarGenerationWindow
        nbw = NewCarGenerationWindow(self.user_id)
        nbw.show()
        self.cmb_car_model.Items.Clear()
        self.cmb_car_generation.Items.Clear()
        self.load_car_brand()

    def on_brand_changed(self, s, e):
        if self.cmb_car_brand.SelectedItem is None:
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM CarModel WHERE brand_id = ? ORDER BY title", (self.cmb_car_brand.SelectedItem.Id,))
        self.cmb_car_model.Items.Clear()
        for row in cur.fetchall():
            self.cmb_car_model.Items.Add(ComboItem(row[0], row[1]))

    def on_model_changed(self, s, e):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM CarGeneration WHERE model_id = ? ORDER BY title", (self.cmb_car_model.SelectedItem.Id,))
        self.cmb_car_generation.Items.Clear()
        for row in cur.fetchall():
            self.cmb_car_generation.Items.Add(ComboItem(row[0], row[1]))

    def save_car(self, sender, e):
        errors = False
        if self.txt_config.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return

        generation_id = self.cmb_car_generation.SelectedItem.Id
        if generation_id is None:
            show_message("Ошибка", "Выберите поколение", "error", "ok")
            return
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("SELECT id FROM CarConfig WHERE generation_id = ? AND description = ?",(generation_id, self.txt_config.Text)).fetchall()
        if temp:
            show_message("Ошибка", "Данная конфигурация уже существует", "error", "ok")
            return
        
        try:
            cur.execute("BEGIN TRANSACTION")
            cur.execute("INSERT INTO CarConfig (description, generation_id) VALUES (?, ?)", (self.txt_config.Text, generation_id))
            conn.commit()
            show_message("Успех", f"Конфигурация {self.txt_config.Text} успешно сохранена!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()