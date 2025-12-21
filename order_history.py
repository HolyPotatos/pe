import sqlite3
import models
from load_XAML import load_xaml
from System.Windows.Input import MouseButtonState
from System.Collections.Generic import List
from System import Object



class OrderHistory:
    def __init__(self, order_id):
        self.window = load_xaml("OrderHistory.xaml")
        self.set_events()
        self.update_data(order_id)

    def set_events(self):
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_exit = self.window.FindName("BtnExit")
        self.border = self.window.FindName("HeaderBorder")
        self.order_status = self.window.FindName("StatusHistoryDataGrid")
        self.payment_status = self.window.FindName("PaymentHistoryDataGrid")
        self.btn_close.Click += lambda s, e: self.window.Close()
        self.btn_exit.Click += lambda s, e: self.window.Close()
        self.border.MouseLeftButtonDown += self.drag_window

    def update_data(self, oid):
        conn = sqlite3.connect("autoparts_shop.db")
        cur = conn.cursor()
        cur.execute("""SELECT osh.id, osh.date_time, oso.title, osn.title, osh.order_id
                    FROM OrderStatusHistory osh
                    LEFT JOIN OrderStatus oso ON oso.id = osh.old_value_id
                    LEFT JOIN OrderStatus osn ON osn.id = osh.new_value_id
                    WHERE order_id = ?
                    """, (oid,))
        self.history_status = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.history_status.Add(models.OrderHistory(*i[:5]))
        self.order_status.ItemsSource = self.history_status
        cur.execute("""SELECT psh.id, psh.date_time, pso.title, psn.title, psh.order_id
                    FROM PaymentStatusHistory psh
                    LEFT JOIN PaymentStatus pso ON pso.id = psh.old_value_id
                    LEFT JOIN PaymentStatus psn ON psn.id = psh.new_value_id
                    WHERE order_id = ?
                    """, (oid,))
        self.history_payment = List[Object]()
        rows = cur.fetchall()
        for i in rows:
            self.history_payment.Add(models.OrderHistory(*i[:5]))
        self.payment_status.ItemsSource = self.history_payment
        conn.close()

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()

    def show(self):
        self.window.ShowDialog()
