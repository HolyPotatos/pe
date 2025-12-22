import sqlite3
import models
from load_XAML import load_xaml
from System.Windows import  Visibility
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class WarehouseView:
    def __init__(self, user_id):
        self.view = load_xaml("WarehouseView.xaml")
        self.set_events()
        self.user_id = user_id
    
    def get_view(self):
        return self.view

    def set_events(self):
        self.dg_all_parts = self.view.FindName("AllPartsDataGrid")
        self.nav_list = self.view.FindName("NavigationList")
        self.btn_back = self.view.FindName("BtnBack")
        self.txt_breadcrumb = self.view.FindName("TxtBreadcrumb")
        self.dg_car_parts = self.view.FindName("CarPartsGrid")
        self.cat_nav_list = self.view.FindName("CatNavigationList")
        self.cat_btn_back = self.view.FindName("CatBtnBack")
        self.cat_txt_breadcrumb = self.view.FindName("CatTxtBreadcrumb")
        self.cat_dg_parts = self.view.FindName("CatPartsGrid")
        self.tab_control = self.view.FindName("MainTabControl")
        self.search = self.view.FindName("SearchBar")
        self.search.TextChanged += self.warehouse_search_changed
        self.nav_list.SelectionChanged += self.on_nav_item_selected
        self.btn_back.Click += self.on_back_click
        self.cat_nav_list.SelectionChanged += self.on_cat_nav_selected
        self.cat_btn_back.Click += self.on_cat_back_click
        self.load_all_parts(None)
        self.reset_car_navigation()
        self.reset_cat_navigation() 

    def warehouse_search_changed(self, s, e):
        if self.search.Text == "":
            self.load_all_parts(None)
        else:
            self.load_all_parts(self.search.Text)        
            
    def load_all_parts(self, filter):
        
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        
        try:
            if filter == None:
                cur.execute("""SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
                FROM AutoPart ap JOIN BrandPart bp ON ap.brand_id = bp.id """)
            else:
                cur.execute("""SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
                FROM AutoPart ap JOIN BrandPart bp ON ap.brand_id = bp.id 
                            WHERE ap.title LIKE ? OR ap.sku LIKE ?""",
                            (f"%{filter}%", f"%{filter}%"))
            rows = cur.fetchall()
            parts = List[Object]()
            for row in rows:
                parts.Add(models.AutoPart(*row))
            self.dg_all_parts.ItemsSource = parts
        except Exception as e:
            show_message("Ошибка", str(e), "error", "ok")
        finally:
            conn.close()

    def reset_car_navigation(self):
        self.nav_history = []
        self.current_level = 0
        self.current_parent_id = None
        self.update_breadcrumb()
        if self.nav_list: self.nav_list.Visibility = Visibility.Visible
        if self.dg_car_parts: self.dg_car_parts.Visibility = Visibility.Collapsed
        if self.btn_back: self.btn_back.Visibility = Visibility.Collapsed
        
        self.load_nav_items(0, None)

    def on_nav_item_selected(self, sender, e):
        selected_item = self.nav_list.SelectedItem
        if selected_item is None: return

        self.nav_history.append((self.current_level, self.current_parent_id, selected_item.Title))
        
        next_level = self.current_level + 1
        self.current_level = next_level
        self.current_parent_id = selected_item.Id

        self.update_breadcrumb()
        self.nav_list.SelectedItem = None 

        if next_level < 4:
            self.load_nav_items(next_level, self.current_parent_id)
            self.btn_back.Visibility = Visibility.Visible
        else:
            self.load_parts_for_config(self.current_parent_id)
            self.nav_list.Visibility = Visibility.Collapsed
            self.dg_car_parts.Visibility = Visibility.Visible
            self.btn_back.Visibility = Visibility.Visible

    def on_back_click(self, sender, e):
        if not self.nav_history: return
        prev_state = self.nav_history.pop()
        self.current_level = prev_state[0]
        self.current_parent_id = prev_state[1] 
        self.update_breadcrumb()
        
        self.dg_car_parts.Visibility = Visibility.Collapsed
        self.nav_list.Visibility = Visibility.Visible
        
        self.load_nav_items(self.current_level, self.current_parent_id)
        
        if self.current_level == 0:
            self.btn_back.Visibility = Visibility.Collapsed

    def update_breadcrumb(self):
        path = " > ".join([item[2] for item in self.nav_history])
        if self.txt_breadcrumb:
            self.txt_breadcrumb.Text = path if path else "Выберите марку"

    def load_nav_items(self, level, parent_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        query = ""
        params = ()

        if level == 0: 
            query = "SELECT id, title FROM CarBrand" 
        elif level == 1: 
            query = "SELECT id, title FROM CarModel WHERE brand_id = ?"
            params = (parent_id,)
        elif level == 2: 
            query = "SELECT id, title FROM CarGeneration WHERE model_id = ?"
            params = (parent_id,)
        elif level == 3:
            query = "SELECT id, description FROM CarConfig WHERE generation_id = ?"
            params = (parent_id,)

        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            items = List[Object]()
            for r in rows:
                items.Add(models.NavigationItem(r[0], str(r[1]), level))
            self.nav_list.ItemsSource = items
        except Exception as e:
            show_message("Ошибка БД", str(e), "error", "ok")
        finally:
            conn.close()

    def load_parts_for_config(self, config_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        query = """
            SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
            FROM AutoPart ap
            JOIN PartCompatibility pc ON ap.id = pc.part_id
            JOIN BrandPart bp ON ap.brand_id = bp.id
            WHERE pc.config_id = ?
        """
        try:
            cur.execute(query, (config_id,))
            rows = cur.fetchall()
            parts = List[Object]()
            for row in rows:
                parts.Add(models.AutoPart(*row))
            self.dg_car_parts.ItemsSource = parts
        except Exception as e:
             show_message("Ошибка", str(e), "error", "ok")
        finally:
            conn.close()

    def reset_cat_navigation(self):
        self.cat_history = []
        self.cat_current_level = 0 
        self.cat_current_parent_id = None
        self.update_cat_breadcrumb()
        
        if self.cat_nav_list: self.cat_nav_list.Visibility = Visibility.Visible
        if self.cat_dg_parts: self.cat_dg_parts.Visibility = Visibility.Collapsed
        if self.cat_btn_back: self.cat_btn_back.Visibility = Visibility.Collapsed
        
        self.load_cat_items(0, None)

    def on_cat_nav_selected(self, sender, e):
        selected = self.cat_nav_list.SelectedItem
        if selected is None: return
        self.cat_history.append((self.cat_current_level, self.cat_current_parent_id, selected.Title))
        self.cat_current_parent_id = selected.Id
        self.cat_current_level += 1
        self.update_cat_breadcrumb()
        self.cat_nav_list.SelectedItem = None

        if self.cat_current_level == 1:
            self.load_cat_items(1, self.cat_current_parent_id)
            self.cat_btn_back.Visibility = Visibility.Visible
        else:
            self.load_parts_by_subcategory(self.cat_current_parent_id)
            self.cat_nav_list.Visibility = Visibility.Collapsed
            self.cat_dg_parts.Visibility = Visibility.Visible
            self.cat_btn_back.Visibility = Visibility.Visible

    def on_cat_back_click(self, sender, e):
        if not self.cat_history: return
        
        prev = self.cat_history.pop()
        self.cat_current_level = prev[0]
        self.cat_current_parent_id = prev[1]
        
        self.update_cat_breadcrumb()
        
        self.cat_dg_parts.Visibility = Visibility.Collapsed
        self.cat_nav_list.Visibility = Visibility.Visible
        
        self.load_cat_items(self.cat_current_level, self.cat_current_parent_id)
        
        if self.cat_current_level == 0:
            self.cat_btn_back.Visibility = Visibility.Collapsed

    def update_cat_breadcrumb(self):
        path = " > ".join([item[2] for item in self.cat_history])
        if self.cat_txt_breadcrumb:
            self.cat_txt_breadcrumb.Text = path if path else "Выберите категорию"

    def load_cat_items(self, level, parent_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        query = ""
        params = ()

        if level == 0:
            query = "SELECT id, title FROM CategoryPart"
        elif level == 1: 
            query = "SELECT id, title FROM SubcategoryPart WHERE category_id = ?"
            params = (parent_id,)

        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            items = List[Object]()
            for r in rows:
                items.Add(models.NavigationItem(r[0], str(r[1]), level))
            self.cat_nav_list.ItemsSource = items
        except Exception as e:
            show_message("Ошибка БД", str(e), "error", "ok")
        finally:
            conn.close()

    def load_parts_by_subcategory(self, subcat_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        query = """SELECT ap.id, ap.sku, ap.title, bp.title, ap.stock, ap.retail_price
            FROM AutoPart ap
            JOIN BrandPart bp ON ap.brand_id = bp.id
            WHERE ap.subcategory_id = ?"""
        try:
            cur.execute(query, (subcat_id,))
            rows = cur.fetchall()
            parts = List[Object]()
            for row in rows:
                parts.Add(models.AutoPart(*row))
            self.cat_dg_parts.ItemsSource = parts
        except Exception as e:
            show_message("Ошибка", str(e), "error", "ok")
        finally:
            conn.close()