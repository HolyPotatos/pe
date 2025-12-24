import sqlite3
import models
from load_XAML import load_xaml
from System.Collections.Generic import List
from System import Object
from message_box import show_message


class UserView:
    def __init__(self, user_id):
        self.view = load_xaml("UserView.xaml")
        self.set_events()
        self.user_id = user_id

    def set_events(self):
        self.selected_user_id = -1
        self.selected_item = None
        self.user_datagrid = self.view.FindName("UserDataGrid")
        self.btn_new_user = self.view.FindName("BtnNewUser")
        self.btn_block_user = self.view.FindName("BtnBlockUser")
        self.tb_search = self.view.FindName("SearchBar")
        self.tb_search.TextChanged += lambda s, e: self.update_data_user()
        self.user_datagrid.SelectionChanged += self.user_selected
        self.btn_new_user.Click += self.new_user_click
        self.btn_block_user.Click += self.block_user_click
        self.update_data_user()

    def get_view(self):
        return self.view

    def new_user_click(self, sender, e):
        from new_user_window import NewUserWindow         
        nw = NewUserWindow(self.user_id)
        nw.show()
        self.update_data_user()

    def user_selected(self, s, e):
        grid = s 
        self.selected_item = grid.SelectedItem
        if self.selected_item is None:
            self.btn_block_user.IsEnabled = False
        else:
            self.btn_block_user.IsEnabled = True
            self.selected_user_id = self.selected_item.Id
            if grid.SelectedItem.Status == "Заблокирован":
                self.btn_block_user.Content = "Разблокировать"
            else:
                self.btn_block_user.Content = "Заблокировать"

    def update_data_user(self):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        if self.tb_search.Text != "":
            cur.execute("""SELECT u.id, u.surname, u.name, u.patronymic, u.email, 
                    u.phone_number, ur.title, ud.login, ud.is_active 
                    FROM User u
                    LEFT JOIN UserAuthData ud ON ud.user_id = u.id
                    LEFT JOIN UserRole ur ON ur.id = u.role_id
                    WHERE u.name LIKE ? OR u.surname LIKE ? OR u.patronymic LIKE ?
                    ORDER BY ud.is_active DESC
                    """, (f"%{self.tb_search.Text}%",f"%{self.tb_search.Text}%",f"%{self.tb_search.Text}%"))
        else:
            cur.execute("""SELECT u.id, u.surname, u.name, u.patronymic, u.email, 
                    u.phone_number, ur.title, ud.login, ud.is_active 
                    FROM User u
                    LEFT JOIN UserAuthData ud ON ud.user_id = u.id
                    LEFT JOIN UserRole ur ON ur.id = u.role_id
                    ORDER BY ud.is_active DESC""")
            
        self.users = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            temp = models.User(*i)
            if i[2] == None:
                temp.DeliveryAddress = "Самовывоз"
            self.users.Add(temp)
        self.user_datagrid.ItemsSource = self.users
        conn.close()
    
    def block_user_click(self, s, e):
        if self.selected_item.Status == "Заблокирован":
            message = "Вы уверены что хотите разблокировать пользователя?"
        else:
            message = "Вы уверены что хотите заблокировать пользователя?"
        if show_message("Предупреждение",message,"warning","yesno") == "yes":
            conn = sqlite3.connect("autoparts_shop.db")
            cur = conn.cursor()
            if  self.selected_item.Status == "Заблокирован":
                cur.execute("UPDATE UserAuthData SET is_active = 1 WHERE user_id = ?", (self.selected_user_id,))
            else:
                cur.execute("UPDATE UserAuthData SET is_active = 0 WHERE user_id = ?", (self.selected_user_id,))
            conn.commit()
            conn.close
            self.update_data_user()
        else:
            return
        