import sys

from filetransfer.core.devicelist import DeviceList
from filetransfer.core.p2p import P2PClient
from filetransfer.client.window import AppWindow

def main():
    # DeviceList().start()
    # P2PClient()
    AppWindow()

if __name__ == "__main__":
    sys.exit(main() or 0)