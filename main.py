import clr

clr.AddReference(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("System.Data")

from System.Threading import Thread, ThreadStart, ApartmentState
from System.Windows import Application
from login_window import LoginWindow


def app_start():
    app = Application()
    window = LoginWindow()
    window.show()
    app.Run()

if __name__ == "__main__":
    t = Thread(ThreadStart(app_start))
    t.SetApartmentState(ApartmentState.STA)
    t.Start()
    t.Join() 