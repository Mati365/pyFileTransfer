class EventHandler:
    def on_device_list_update(self, device_list):
        """ On update device list
        :param device_list: List of all devices
        """
        pass

    def on_file_copying_progress(self, to_ip, file, percent, total_percent):
        """ On copying progress
        :param to_ip:               Receiver IP
        :param file:                Path to file
        :param percentage:          Percent of copy
        :param total_percentage:    Total copied bytes
        """
        pass

    def on_accept_connection_prompt(self, ip, thread):
        """ Accept connection prompt
        :param ip:      Client ip
        :param thread:  Client thread
        """
        pass

    def on_refuse_connection_prompt(self):
        """ Refuse connection prompt
        """
        pass