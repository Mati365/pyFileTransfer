import urllib

from gi.repository import Gtk, Gdk, GObject
from urllib.parse import urlparse

from ..core.p2p import P2PClient
from ..core.events import EventHandler

def show_msg_box(parent, title, message, buttons=Gtk.ButtonsType.OK_CANCEL, type=Gtk.MessageType.WARNING):
    """ Show message box
    :param parent:  Parent window
    :param title:   Title
    :param message: Content
    :param buttons: Buttons
    :param type:    Icon type
    :return: MessageBox value
    """
    dialog = Gtk.MessageDialog(parent, 0, type, buttons, title)
    dialog.format_secondary_text(message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK

class FileList(list):
    def __init__(self):
        list.__init__(self)
        self.total_size = 0
        self.total_files = 0

    def append(self, files):
        self.total_size += files[1]
        self.total_files += len(files[0])
        list.append(self, files)

class AppWindow(Gtk.Window, EventHandler):
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

        self.p2p = P2PClient(self)
        Gtk.main()

    # UI
    def __create_client_list_panel(self):
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(150, -1)

        self.clients = Gtk.ListStore(str, bool)
        clients_view = Gtk.TreeView(self.clients)
        def cell_toggled(cell_renderer, path):
            self.clients[path][1] = not self.clients[path][1]

        toggle_renderer = Gtk.CellRendererToggle()
        toggle_renderer.connect("toggled", cell_toggled)
        clients_view.append_column(Gtk.TreeViewColumn("", toggle_renderer, active=1))
        clients_view.append_column(Gtk.TreeViewColumn("Device", Gtk.CellRendererText(), text=0))

        scrolled_window.add(clients_view)
        return scrolled_window

    def __create_file_list_panel(self):
        v_box = Gtk.VBox(spacing=6)

        # List of files
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.files = Gtk.ListStore(str, str, str)
        files_view = Gtk.TreeView(self.files)
        files_view.set_size_request(-1, 128)
        files_view.append_column(Gtk.TreeViewColumn("Size", Gtk.CellRendererText(), text=0))
        files_view.append_column(Gtk.TreeViewColumn("File", Gtk.CellRendererText(), text=1))
        files_view.append_column(Gtk.TreeViewColumn("Directory", Gtk.CellRendererText(), text=2))

        scrolled_window.add(files_view)
        v_box.pack_start(scrolled_window, True, True, 0)

        # Files info info bar
        h_box = Gtk.HBox(spacing=6)
        v_box.pack_start(h_box, False, True, 0)

        self.total_size_label = Gtk.Label("", xalign=0.0)
        h_box.pack_start(self.total_size_label, True, True, 0)
        self.total_files_label = Gtk.Label("", xalign=0.0)
        h_box.pack_start(self.total_files_label, False, True, 0)

        # Toolbar
        toolbar = Gtk.Toolbar()
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)
        toolbar.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        v_box.pack_start(toolbar, False, True, 0)

        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_OPEN), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_SAVE), -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_ADD), -1)
        toolbar.insert(Gtk.ToolButton(Gtk.STOCK_DELETE), -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)

        send = Gtk.ToolButton(Gtk.STOCK_EXECUTE)
        send.connect("clicked", self.__send_files)
        toolbar.insert(send, -1)

        self._reload_file_list()
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

    def __send_files(self, button):
        for ip in [client[0] for client in self.clients if client[1]]:
            self.p2p.send_files(ip, self.file_list)

    def _reload_file_list(self):
        self.total_files_label.set_text("Files: {}".format(self.file_list.total_files))
        self.total_size_label.set_text("Total size: {}".format(AppWindow.get_text_size(self.file_list.total_size)))

        self.files.clear()
        for nested_list in self.file_list:
            for file in nested_list[0]:
                self.files.append([AppWindow.get_text_size(file[1]), file[0], nested_list[2]])

    # Messages
    def __on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
        for url in urllib.parse.unquote(data.get_data().decode("UTF-8")).splitlines():
            self.file_list.append(P2PClient.list_files(urlparse(url).path))
        self._reload_file_list()

    def on_device_list_update(self, devices):
        self.clients.clear()
        for ip in devices:
            self.clients.append([ip, False])

    def on_accept_connection_prompt(self, ip, thread):
        def runner():
            if show_msg_box(self, "Connection", "Incoming connection from {}. Accept?".format(ip)):
                thread.accept_connection()
            else:
                thread.refuse_connection()
            return False

        GObject.idle_add(runner)

    def on_refuse_connection_prompt(self):
        GObject.idle_add(show_msg_box, self, "Connection", "Receiver refused the connection!", Gtk.ButtonsType.CANCEL)
