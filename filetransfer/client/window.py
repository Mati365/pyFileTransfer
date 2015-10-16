import urllib

from gi.repository import Gtk, Gdk
from urllib.parse import urlparse

from ..core.p2p import P2PClient

class AppWindow(Gtk.Window):
    def __init__(self):
        super(AppWindow, self).__init__(title="FileTransfer")

        self.set_resizable(False)
        self.set_size_request(500, 500)
        self.set_border_width(10)

        self.__configure_drag_drop()
        self.__create_layout()

        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        Gtk.main()

    def __create_layout(self):
        h_box = Gtk.Box(spacing=6)
        self.add(h_box)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.files = Gtk.TreeView(Gtk.ListStore(str, str, str))
        self.files.set_size_request(-1, 128)
        self.files.append_column(Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=0))
        self.files.append_column(Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=1))
        self.files.append_column(Gtk.TreeViewColumn("Directory", Gtk.CellRendererText(), text=2))

        scrolled_window.add(self.files)
        h_box.pack_start(scrolled_window, True, True, 0)

    def __configure_drag_drop(self):
        self.drag_dest_set(0, [], 0)
        self.connect("drag-motion", lambda widget, context, x, y, time:(
              Gdk.drag_status(context, Gdk.DragAction.COPY, time)
            , True
        ))
        self.connect("drag-drop", lambda widget, context, x, y, time:(
            widget.drag_get_data(context, context.list_targets()[-1], time)
        ))
        self.connect("drag-data-received", self.__on_drag_data_received)

    def __on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        def get_text_size(bytes):
            for unit in ["B", "KB", "MB", "GB"]:
                if bytes < 1024.0:
                    return "{0:.2f}{1}".format(bytes, unit)
                bytes /= 1024.0

        model = self.files.get_model()
        for url in urllib.parse.unquote(data.get_data().decode("UTF-8")).splitlines():
            files = P2PClient.list_files(urlparse(url).path)
            for file in files[0]:
                model.append([get_text_size(file[1]), file[0], files[2]])