import bambulabs_api as bl
import threading
import time

class Printer:
    """
    mostly just an allocation wrapper. there's definitely a better way to do this
    """
    def __init__(self, ip, access, serial):
        self.printer = bl.Printer(ip, access, serial)
        self.users = 0
    def alloc(self):
        self.users += 1
        print("alloc", self.users)
        if self.users == 1:
            self.printer.connect()
            time.sleep(2)
    def dealloc(self):
        self.users -= 1
        print("dealloc", self.users)
        if self.users <= 0:
            self.printer.disconnect()
            # refresh cam client to solve threading issue
            self.printer.camera_client = bl.camera_client.PrinterCamera(self.printer.ip_address, self.printer.access_code)
            self.users = 0
    def home(self):
        self.printer.home_printer()
    def get_camera_image(self):
        image = self.printer.get_camera_image()
        return image
    def gcode(self, *args, **kwargs):
        self.printer.gcode(*args, **kwargs)
