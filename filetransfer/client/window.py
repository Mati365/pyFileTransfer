from gi.repository import Gtk, GObject, Gdk

class AppWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="pyFileTransfer")

        self.set_border_width(10)
        self.set_size_request(256, 350)
        print(Gdk)
        # self.set_type_hint(Gtk.gdk.WINDOW_TYPE_HINT_POPUP_MENU)
        self.connect("delete-event", Gtk.main_quit)
        self.show_all()