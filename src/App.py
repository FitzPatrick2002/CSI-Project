import serial
from typing import List, Tuple, Dict
import re
import threading
from time import sleep

from GUI import TkApp

from PortsRegistry import PortsRegistry
from ListPortInfoWrapper import ListPortInfoWrapper

from Menu import Menu

class App:

    def __init__(self):

        self._gui = TkApp()
        self._gui.master.title("COM - MANAGER")

        self._gui_thread = threading.Thread(target=self.run_gui, name="GUI")

    # --------- Threading --------- #

    def run(self):
        self.run_gui()
        
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

class Services:
    ''' Stores services which operate on COM wrappers and registry. '''

