from gi.repository import Gtk, Gdk
from urllib.parse import urlparse

from ..core.p2p import P2PClient

class AppWindow(Gtk.Window):
    def __init__(self):
        super(AppWindow, self).__init__(title='FileTransfer')

        self.__configure_drag_drop()
        self.connect("delete-event", Gtk.main_quit)
        self.show()
        Gtk.main()

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
        for url in data.get_data().decode("UTF-8").splitlines():
            print(P2PClient.list_files(urlparse(url).path))