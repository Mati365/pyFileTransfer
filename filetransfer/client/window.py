import urllib

from gi.repository import Gtk, Gdk
from urllib.parse import urlparse

from ..core.p2p import P2PClient

class FileList:
    def __init__(self):
        self.list = [([], 0, "")]
        self.total_size = 0
        self.total_files = 0

    def append(self, files):
        self.list.append(files)
        self.total_size += files[1]
        self.total_files += len(files[0])

    def __iter__(self):
        return iter(self.list)

class AppWindow(Gtk.Window):
    def __init__(self):
        super(AppWindow, self).__init__(title="FileTransfer")

        self.file_list = FileList()

        self.set_resizable(False)
        self.set_size_request(400, 300)
        self.set_border_width(6)

        self.__configure_drag_drop()
        self.__create_layout()

        self.connect("delete-event", Gtk.main_quit)
        self.show_all()
        Gtk.main()

    def __create_client_list_panel(self):
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(150, -1)

        model = Gtk.ListStore(str, bool)
        model.append(["192.168.1.1", False])
        model.append(["192.168.1.10", False])
        model.append(["192.168.1.16", False])
        model.append(["192.168.1.13", False])

        self.clients = Gtk.TreeView(model)

        def cell_toggled(cell_renderer, path):
            model[path][1] = not model[path][1]

        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", cell_toggled)
        self.clients.append_column(Gtk.TreeViewColumn("", toggle_renderer, active=1))
        self.clients.append_column(Gtk.TreeViewColumn("Device", Gtk.CellRendererText(), text=0))

        scrolled_window.add(self.clients)
        return scrolled_window

    def __create_file_list_panel(self):
        # List of files
        v_box = Gtk.VBox(spacing=6)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.files = Gtk.TreeView(Gtk.ListStore(str, str, str))
        self.files.set_size_request(-1, 128)
        self.files.append_column(Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=0))
        self.files.append_column(Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=1))
        self.files.append_column(Gtk.TreeViewColumn("Directory", Gtk.CellRendererText(), text=2))

        scrolled_window.add(self.files)
        v_box.pack_start(scrolled_window, True, True, 0)

        # Files info info bar
        h_box = Gtk.HBox(spacing=6)
        v_box.pack_start(h_box, False, True, 0)

        self.total_size_label = Gtk.Label("", xalign=0.0)
        h_box.pack_start(self.total_size_label, True, True, 0)
        self.total_files_label = Gtk.Label("", xalign=0.0)
        h_box.pack_start(self.total_files_label, False, True, 0)

        self._reload_file_list()

        # Toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        toolbar.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)

        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_OPEN), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_SAVE), -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_ADD), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_DELETE), -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_EXECUTE), -1)

        v_box.pack_start(toolbar, False, True, 0)
        return v_box

    def __create_layout(self):
        h_box = Gtk.HBox(spacing=6)
        h_box.pack_start(self.__create_client_list_panel(), True, True, 0)
        h_box.pack_start(self.__create_file_list_panel(), True, True, 0)
        self.add(h_box)

    def __configure_drag_drop(self):
        self.drag_dest_set(0, [], 0)
        self.connect("drag-motion", lambda widget, context, x, y, time:(
              Gdk.drag_status(context, Gdk.DragAction.COPY, time)
            , True
        ))
        self.connect("drag-drop", lambda widget, context, x, y, time:(
              widget.drag_get_data(context, context.list_targets()[-1], time)
            , context.finish(True, False, time)
        ))
        self.connect("drag-data-received", self.__on_drag_data_received)

    @staticmethod
    def get_text_size(bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return "{0:.2f}{1}".format(bytes, unit)
            bytes /= 1024.0

    def _append_files(self, file_list):
        self.file_list.append(file_list)

    def _reload_file_list(self):
        self.total_files_label.set_text("Files: {}".format(self.file_list.total_files))
        self.total_size_label.set_text("Total size: {}".format(AppWindow.get_text_size(self.file_list.total_size)))

        model = self.files.get_model()
        model.clear()
        for nested_list in self.file_list:
            for file in nested_list[0]:
                model.append([AppWindow.get_text_size(file[1]), file[0], nested_list[2]])

    def __on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        for url in urllib.parse.unquote(data.get_data().decode("UTF-8")).splitlines():
            self._append_files(P2PClient.list_files(urlparse(url).path))
        self._reload_file_list()