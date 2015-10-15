class EventHandler:
    def on_device_list_update(self, device_list):
        """ On update device list
        :param device_list: List of all devices
        """
        pass

    def on_file_copying_progress(self, file, percent, total_percent):
        """ On copying progress
        :param file:                Path to file
        :param percentage:          Percent of copy
        :param total_percentage:    Total copied bytes
        """
        pass