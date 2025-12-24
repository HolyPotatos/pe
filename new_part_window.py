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

class NewPartWindow:
    def __init__(self, user_id, part_id = -1):
        self.window = load_xaml("NewPartWindow.xaml")
        self.user_id = user_id
        self.set_events()
        self.load_part_brand()
        if part_id != -1:
           self.set_edit(part_id)
        self.edit_part_id = part_id

    def set_edit(self, part_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT title, sku, retail_price, brand_id, category_id, subcategory_id FROM AutoPart WHERE id = ?", (part_id,))
        title, sku, price, brand_id, category_id, subcategory_id = cur.fetchone()
        self.txt_title.Text = title
        self.txt_sku.Text = sku
        self.txt_price.Text = str(price)
        for item in self.cmb_brand.Items:
            if item.Id == brand_id:
                self.cmb_brand.SelectedItem = item
                break
        for item in self.cmb_category.Items:
            if item.Id == category_id:
                self.cmb_category.SelectedItem = item
                break
        for item in self.cmb_subcategory.Items:
            if item.Id == subcategory_id:
                self.cmb_subcategory.SelectedItem = item
                break
        

    def set_events(self):
        self.cmb_brand = self.window.FindName("BrandComboBox")
        self.cmb_category = self.window.FindName("CategoryComboBox")
        self.cmb_subcategory = self.window.FindName("SubcategoryComboBox")
        self.border = self.window.FindName("TitleBar")
        self.txt_sku = self.window.FindName("SKUTextBox")
        self.txt_title = self.window.FindName("TitleTextBox")
        self.txt_price = self.window.FindName("PriceTextBox")
        self.btn_save = self.window.FindName("BtnSave")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_cancel = self.window.FindName("BtnCancel")
        self.btn_add_brand = self.window.FindName("BtnAddBrand")
        self.cmb_category.SelectionChanged += self.on_category_changed
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_save.Click += self.save_brand
        self.btn_add_brand.Click += self.new_brand_click
        self.btn_cancel.Click += lambda s, e: self.window.Close()
        self.btn_close.Click += lambda s, e: self.window.Close()

    def show(self):
        self.window.ShowDialog() 

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()    

    def load_part_brand(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM BrandPart ORDER BY title")
        for row in cur.fetchall():
            self.cmb_brand.Items.Add(ComboItem(row[0], row[1]))
        cur.execute("SELECT id, title FROM CategoryPart ORDER BY title")
        for row in cur.fetchall():
            self.cmb_category.Items.Add(ComboItem(row[0], row[1]))

        conn.close()
        self.cmb_brand.SelectedIndex = 0
        self.cmb_category.SelectedIndex = 0
    
    def new_brand_click(self, s, e):
        from new_brand_window import NewBrandWindow
        nbw = NewBrandWindow(self.user_id)
        nbw.show()
        self.load_part_brand()

    def on_category_changed(self, s, e):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM SubcategoryPart WHERE category_id = ? ORDER BY title", (self.cmb_category.SelectedItem.Id,))
        self.cmb_subcategory.Items.Clear()
        for row in cur.fetchall():
            self.cmb_subcategory.Items.Add(ComboItem(row[0], row[1]))
        self.cmb_subcategory.SelectedIndex = 0

    def save_brand(self, sender, e):
        errors = False
        if self.txt_sku.Text == "": errors = True
        if self.txt_title.Text == "": errors = True
        if self.txt_price.Text == "": errors = True
        if errors:
            show_message("Ошибка", "Заполните все поля", "error", "ok")
            return
        
        try:
            price = int(self.txt_price.Text)
            if price <= 0: raise ValueError
        except:
            show_message("Ошибка", "Введите корректную цену", "error", "ok")
            return

        brand_id = self.cmb_brand.SelectedItem.Id
        category_id = self.cmb_category.SelectedItem.Id
        subcategory_id = self.cmb_category.SelectedItem.Id
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        temp = cur.execute("SELECT id FROM AutoPart WHERE sku = ? AND id != ?",(self.txt_sku.Text, self.edit_part_id)).fetchall()
        if temp:
            show_message("Ошибка", "Товар с таким SKU уже существует", "error", "ok")
            return
        
        try:
            cur.execute("BEGIN TRANSACTION")
            if self.edit_part_id == -1:
                cur.execute("INSERT INTO AutoPart (title, sku, retail_price, stock, brand_id, category_id, subcategory_id) VALUES (?, ?, ?, 0, ?, ?, ?)", 
                (self.txt_title.Text, self.txt_sku.Text, self.txt_price.Text, brand_id, category_id, subcategory_id))
            else:
                cur.execute("UPDATE AutoPart SET title = ?, sku = ?, retail_price = ?, brand_id = ?, category_id = ?, subcategory_id = ? WHERE id = ?", 
                            (self.txt_title.Text, self.txt_sku.Text, self.txt_price.Text, brand_id, category_id, subcategory_id, self.edit_part_id))
            conn.commit()
            show_message("Успех", f"Товар {self.txt_sku.Text} успешно сохранен!", "info", "ok")
            self.window.Close()
            
        except Exception as ex:
            conn.rollback()
            show_message("Ошибка сохранения", str(ex), "error", "ok")
        finally:
            conn.close()