import sys

from filetransfer.client.devicelist import DeviceList
from filetransfer.client.p2p import P2PClient

def main():
    DeviceList().start()
    P2PClient()

if __name__ == "__main__":
    sys.exit(main() or 0)