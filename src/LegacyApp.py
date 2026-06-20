import serial
from typing import List, Tuple, Dict
import re
import threading

from GUI import TkApp

from PortsRegistry import PortsRegistry
from ListPortInfoWrapper import ListPortInfoWrapper

from Menu import Menu

class App:

    def __init__(self):
        self.registry = PortsRegistry()

        self._routes = {
            "List Ports"     : self.list_ports,
            "Port Info"      : self.port_info,
            "Refresh Ports"  : self.refresh_registry,
            "Configure Port" : self.configure_port 
        }

        self._menu = Menu(self._routes)
        self._gui = TkApp()
        self._gui.master.title("COM - MANAGER")

        self._gui_thread = threading.Thread(target=self.run_gui, name="GUI")

    def run(self):
        self.launch_threads()
        self._menu.loop()
        self.collect_threads()
        
    def launch_threads(self):
        self._gui_thread.start()

    def collect_threads(self):
        self._gui_thread.join()

    def run_gui(self):
        ''' Runs the GUI loop. '''
        try:
            self._gui.mainloop()
        except Exception as e:
            print(f"ERROR in run_gui(): {e}.")
        finally:
            print("Exiting run_gui().")

    def list_ports(self):
        ''' Prints names of all avaialable COM ports. '''
        for idx, port in enumerate(self.registry.get_ports_names()):
            print(f"{idx}. {port}")

    def port_info(self):
        ''' Prints info about specific COM port. '''

        # 0. Select port (name)

        print("Port: ", end="")
        port = input()

        if not port in self.registry.get_ports_names():
            print(f"ERROR: Unknown port {port}. Avaialable ports: {' '.join(self.registry.get_ports_names())}.")
            return

        # 1. Select info type

        print("Info type: ", end="")
        info = input()

        # 2. Print info

        info = info.strip()
        if info:
            info = info.split(sep=" ")

        port = self.registry.get_port(port)
        if port:
            port.print_info(info)
        
    def refresh_registry(self):
        ''' Refreshes the self.registry with. '''
        self.registry.refresh()

    def configure_port(self):
        ''' Configures a specified COM port. 
            Config: pdu:<PDU> bauds:<value> flow:[xon-xoff, dtr-dsr, rts-cts, ' '] term:[CR, LF, CR-LF, <custom>]
            PDU: 8N1, 8N0, ...
            custom: custom 2 character byte sequence

        '''

        # 0. Specify COM port
        
        print("Port: ", end="")
        port = input()

        if not port in self.registry.get_ports_names():
            print(f"ERROR: Unknown port {port}. Avaialable ports: {' '.join(self.registry.get_ports_names())}.")
            return
            
        # 1. Specify configuration

        print("Configuration: ")
        config = input()

        if not config.strip():
            print("No config specified, skipping.")
            return
        
        # 2. Parse config 
        pattern = re.compile("\\s*(?:baud:(?P<baud>\\d+))?\\s*"
                             "(?:flow:(?P<flow>xonxoff|rtscts|dsrdtr))?\\s*"
                             "(?:pdu:(?P<pdu>[5678][NOEMS][012]))?\\s*"
                             "(?:term:(?P<term>CR|LF|CR-LF|\\w{2}))?\\s*"
                            )
        m = pattern.match(config)

        # 2.1 Settings setup

        ser = serial.Serial(port=port)
        settings = ser.get_settings()

        if m["baud"]:
            settings["baudrate"] = int(m["baud"])

        if m["flow"]:
            settings["xonxoff"] = False
            settings["dsrdtr"]  = False
            settings["rtscts"]  = False
            settings[m["flow"]] = True

        if m["pdu"]:
            pdu_str = m["pdu"]
            settings["bytesize"] = int(pdu_str[0])
            settings["parity"]   = pdu_str[1]

            stopbits = {
                "0" : serial.STOPBITS_ONE,
                "1" : serial.STOPBITS_ONE_POINT_FIVE,
                "2" : serial.STOPBITS_TWO
            }

            settings["stopbits"] = stopbits[pdu_str[2]]

        if m["term"]:
            pass

        ser.apply_settings(settings)
        print(ser.get_settings())
