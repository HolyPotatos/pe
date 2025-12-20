from System.Windows import Visibility
from System.Windows.Input import MouseButtonState
from load_XAML import load_xaml

class CustomMessageBox:
    def __init__(self):
        self.window = load_xaml("MessageBox.xaml")
        self.result = None
        self.set_events() 

    def set_events(self):
        self.border = self.window.FindName("HeaderBorder")
        self.title_text = self.window.FindName("TitleText")
        self.message_text = self.window.FindName("MessageText")
        self.icon_info = self.window.FindName("IconInfo")
        self.icon_warning = self.window.FindName("IconWarning")
        self.icon_error = self.window.FindName("IconError")
        self.btn_close = self.window.FindName("BtnClose")
        self.btn_ok = self.window.FindName("BtnOk")
        self.btn_yes = self.window.FindName("BtnYes")
        self.btn_no = self.window.FindName("BtnNo")
        self.border.MouseLeftButtonDown += self.drag_window
        self.btn_close.Click += lambda s, e: self.set_result(None) 
        self.btn_ok.Click += lambda s, e: self.set_result("ok")
        self.btn_yes.Click += lambda s, e: self.set_result("yes")
        self.btn_no.Click += lambda s, e: self.set_result("no")

    def drag_window(self, sender, e):
        if e.LeftButton == MouseButtonState.Pressed:
            self.window.DragMove()

    def set_result(self, value):
        self.result = value
        self.window.Close()

    def show(self, title, message, msg_type = "info", buttons = "OK"):
        self.title_text.Text = title
        self.message_text.Text = message
        self.icon_info.Visibility = Visibility.Collapsed
        self.icon_warning.Visibility = Visibility.Collapsed
        self.icon_error.Visibility = Visibility.Collapsed
        if msg_type.lower() == "warning":
             self.icon_warning.Visibility = Visibility.Visible
        elif msg_type.lower() == "error":
             self.icon_error.Visibility = Visibility.Visible
        else:
             self.icon_info.Visibility = Visibility.Visible
        self.btn_ok.Visibility = Visibility.Collapsed
        self.btn_yes.Visibility = Visibility.Collapsed
        self.btn_no.Visibility = Visibility.Collapsed
        mode = buttons.lower()
        if mode == "ok":
            self.btn_ok.Visibility = Visibility.Visible
        elif mode == "yesno":
            self.btn_yes.Visibility = Visibility.Visible
            self.btn_no.Visibility = Visibility.Visible
        self.window.ShowDialog()
        return self.result


def show_message(title, message, msg_type="info", buttons="OK"):
    msg_box = CustomMessageBox()
    return msg_box.show(title, message, msg_type, buttons)