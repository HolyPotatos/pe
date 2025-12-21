import sqlite3
import models
from datetime import datetime
from load_XAML import load_xaml
from System.Windows import WindowState, Visibility
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class MainWindow:
    def __init__(self, user_id):
        self.window = load_xaml("MainWindow.xaml")
        self.set_main_events()
        self.order_content = load_xaml("OrdersView.xaml")
        self.set_order_events()
        self.warehouse_content = load_xaml("WarehouseView.xaml")
        self.set_warehouse_events()
        self.navigate(self.order_content)
        self.update_data_order()
        self.user_id = user_id
    
    #Главное окно

    def set_main_events(self):
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_minimized = self.window.FindName("BtnMinimized")
        self.btn_maximized = self.window.FindName("BtnMaximized")
        self.rbtn_warehouse = self.window.FindName("RBtnWarehouseRadio")
        self.rbtn_order = self.window.FindName("RBtnOrderRadio")
        self.btn_logout = self.window.FindName("BtnLogout")
        self.content_control = self.window.FindName("MainContentControl")
        self.btn_close.Click += lambda s, e: self.window.Close()
        self.btn_minimized.Click += self.minimized_window
        self.btn_maximized.Click += self.maximized_window
        self.btn_logout.Click += self.logout
        self.rbtn_order.Click += lambda s, e: self.navigate(self.order_content)
        self.rbtn_warehouse.Click += lambda s, e: self.navigate(self.warehouse_content)


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
    
    #Страница заказов (Продавец)

    def set_order_events(self):
        self.selected_order_id = -1
        self.order_datagrid = self.order_content.FindName("OrderDataGrid")
        self.order_part_datagrid = self.order_content.FindName("OrderPartsDataGrid")
        self.btn_new_order = self.order_content.FindName("BtnNewOrder")
        self.btn_order_cancel = self.order_content.FindName("BtnOrderCansel")
        self.btn_order_history = self.order_content.FindName("BtnOrderHistory")
        self.tb_search = self.order_content.FindName("SearchBar")
        self.tb_search.TextChanged += lambda s, e: self.update_data_order()
        self.order_datagrid.SelectionChanged += self.on_order_selected
        self.btn_order_cancel.Click += self.on_order_cansel_click
        self.btn_order_history.Click += self.on_history_click
        self.btn_new_order.Click += self.open_new_order_window

    def open_new_order_window(self, sender, e):
        from new_order_window import NewOrderWindow         
        nw = NewOrderWindow(self.user_id)
        nw.show()
        self.update_data_order()

    def on_order_selected(self, s, e):
        grid = s 
        selected_item = grid.SelectedItem
        if selected_item is None:
            self.btn_order_cancel.IsEnabled = False
            self.btn_order_history.IsEnabled = False
        else:
            self.btn_order_cancel.IsEnabled = True
            self.btn_order_history.IsEnabled = True
            self.update_data_order_parts(selected_item.ID)
            self.selected_order_id = selected_item.ID

    def update_data_order_parts(self, order_id):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT op.part_id, p.sku, p.title, op.order_id, op.count, op.unit_retail_price
                    FROM OrderParts op
                    JOIN AutoPart p ON op.part_id = p.id
                    WHERE op.order_id = ?
                    """,(order_id,))
        self.orders_parts = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.orders_parts.Add(models.OrderParts(*i[:7]))
        self.order_part_datagrid.ItemsSource = self.orders_parts
        conn.close()

    def update_data_order(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        if self.tb_search.Text != "":
            cur.execute("""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    WHERE o.delivery_address LIKE ?
                    ORDER BY o.date, os.title DESC
                    """, (f"%{self.tb_search.Text}%",))
        else:
            cur.execute("""SELECT o.id, o.date, o.delivery_address, o.seller_id, o.storekeeper_id, 
                    dt.title, os.title, pt.title, 
                    (SELECT SUM(op.unit_retail_price * op.count) FROM OrderParts op WHERE order_id = o.id) as total_price
                    FROM Orders o
                    JOIN DeliveryType dt ON dt.id = o.delivery_type_id
                    JOIN OrderStatus os ON os.id = o.order_status_id
                    JOIN PaymentType pt ON pt.id = o.payment_type_id
                    ORDER BY o.date DESC, os.title ASC""")
            
        self.orders = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            temp = models.Orders(*i)
            if i[2] == None:
                temp.DeliveryAddress = "Самовывоз"
            self.orders.Add(temp)
        self.order_datagrid.ItemsSource = self.orders
        conn.close()
    
    def on_order_cansel_click(self, s, e):
        if show_message("Предупреждение","Вы уверены что хотите отменить заказ?","warning","yesno") == "yes":
            conn = sqlite3.connect("autoparts_shop.db")
            cur = conn.cursor()
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            old_value_id = int(cur.execute("SELECT order_status_id FROM Orders WHERE id = ?", (self.selected_order_id,)).fetchone()[0])
            if old_value_id == 5:
                show_message("Ошибка","Заказ уже отменён","error","ok")
                return
            cur.execute("INSERT INTO OrderStatusHistory (date_time, old_value_id, new_value_id, order_id) VALUES (?,?,?,?) ", (current_date, old_value_id, 5, self.selected_order_id))
            cur.execute("UPDATE Orders SET order_status_id = 5 WHERE id = ?", (self.selected_order_id,))
            conn.commit()
            conn.close
            self.update_data_order()
        else:
            return
        
    def on_history_click(self, s, e):
        from order_history import OrderHistory
        ohis = OrderHistory(self.selected_order_id)
        ohis.show()

    def on_search_changed(self, s, e):
        self.update_data_order

    #Страница склада (Продавец)

    def set_warehouse_events(self):
        self.dg_all_parts = self.warehouse_content.FindName("AllPartsDataGrid")
        self.nav_list = self.warehouse_content.FindName("NavigationList")
        self.btn_back = self.warehouse_content.FindName("BtnBack")
        self.txt_breadcrumb = self.warehouse_content.FindName("TxtBreadcrumb")
        self.dg_car_parts = self.warehouse_content.FindName("CarPartsGrid")
        self.cat_nav_list = self.warehouse_content.FindName("CatNavigationList")
        self.cat_btn_back = self.warehouse_content.FindName("CatBtnBack")
        self.cat_txt_breadcrumb = self.warehouse_content.FindName("CatTxtBreadcrumb")
        self.cat_dg_parts = self.warehouse_content.FindName("CatPartsGrid")
        self.tab_control = self.warehouse_content.FindName("MainTabControl")
        self.search = self.warehouse_content.FindName("SearchBar")
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