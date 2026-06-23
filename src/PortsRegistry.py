import serial
import serial.tools.list_ports
from ListPortInfoWrapper import ListPortInfoWrapper
from typing import Dict, List, Any
import threading
from time import sleep
import utils
from queue import Queue, Empty
from AppState import AppState

class PortsRegistry:
    ''' Stores a dictionary of all avaialable ports. 
    
    Attributes:
    ports_map    : Dict of all ports information objects. (key, value) = (port name, ListPortInfoWrapper object)
    current_port : Currently open port
    '''
    def __init__(self, app_state : AppState):
        self.state = app_state

        self.ports_map : Dict[str, ListPortInfoWrapper] = {}
        self._ports_lock = threading.Lock()
        self.refresh()

        self.current_port = None
        self.current_port_lock = threading.RLock()

        self.listenning_thread : threading.Thread = None

        self.terminator = ""

        self.modbus_write_queue = Queue()
        self.modbus_write_thread = threading.Thread(target=self.modbus_write_thread_body, daemon=True)
        self.modbus_write_thread.start()

    # ---------------- Port Discovery ---------------- #

    def refresh(self):
        ''' Fetches all avaialable ports & stores them in self.ports_map as ListPortInfoWrapper's. '''
        with self._ports_lock:
            self.ports_map.clear()

            ports = [ListPortInfoWrapper(p) for p in serial.tools.list_ports.comports()]
            
            for port in ports:
                self.ports_map[port.name] = port
            
    def get_device_info(self, name : str) -> None | ListPortInfoWrapper:
        return self.ports_map.get(name)

    def get_ports_names(self) -> List[str]:
        return list(self.ports_map.keys())

    # ---------------- Port Opeartions ---------------- #

    # --- Open / Close port --- #

    def open_port(self, name : str) -> serial.Serial | None:
        ''' Opens a COM port with specified name. '''

        if name not in self.get_ports_names():
            return None

        with self.current_port_lock:
            if self.current_port and self.current_port.is_open:
                self.current_port.close()
            self.current_port = serial.Serial(port = name, timeout=0.1)
            return self.current_port

    def is_port_open(self) -> bool:
        return self.current_port and self.current_port.is_open

    def close_port(self):
        ''' Closes currently open port. '''

        with self.current_port_lock: 
            if self.current_port and self.current_port.is_open:
                self.current_port.close()
                self.current_port = None
    
    # --- DTR / RTS --- #

    def toggle_dtr(self):
        if self.current_port:
            with self.current_port_lock:
                self.current_port.dtr = not self.current_port.dtr
                return self.current_port.dtr
    
    def toggle_rts(self):
        if self.current_port:
            with self.current_port_lock:
                self.current_port.rts = not self.current_port.rts
                return self.current_port.rts
    
    # --- Terminator --- # 

    @property
    def terminator(self):
        return self.__terminator

    @terminator.setter
    def terminator(self, val : str):
        with self.current_port_lock:
            self.__terminator = utils.terminator_map[val] if val in utils.terminator_map.keys() else val

    # --- Communication --- #

    def start_listenning_on_port(self, func : callable = None):
        ''' 
        Starts a new thread which listens if there are any messages incoming. 
        
        Args:
        - func (callable) : Function passed to _listen_on_port().
        '''

        self.listenning_thread = threading.Thread(target=self._listen_on_port, args=(func,),daemon=True)
        print("Starting thread")
        self.listenning_thread.start()
        return 
    
        if not self.listenning_thread.is_alive():
            print("Starting to listen")
            self.current_port.reset_input_buffer()
            self.listenning_thread_run = True
            self.listenning_thread = threading.Thread(target=lambda : self._listen_on_port(func=func), daemon=True)
            self.listenning_thread.start()

    def send_msg(self, message : str):
        ''' Sends message with appended terminator via COM port. '''
        txt = message + self.terminator
        with self.current_port_lock:
            self.current_port.write(message.encode("utf-8"))

    def send_modbus_ascii(self, address : int, command : int, data : str):
        message = utils.prepare_modbus_ascii_message(address, command, data)
        self.modbus_write_queue.put(message)

    def modbus_write_thread_body(self):
        while True:
            attempt = 0
            try:
                message = self.modbus_write_queue.get(block=True, timeout=1.0)
            except Empty:
                continue

            with self.current_port_lock:
                if self.current_port and self.current_port.is_open:
                    while attempt < self.state.modbus_retransmissions:
                        try:
                            self.current_port.write(message)
                            break
                        except TimeoutError:
                            attempt += 1

    # --- Port Operations --- #

    def apply_method_on_port(self, name : str, args : Dict[str, Any]=None) -> Any | None:
        if not self.current_port:
            return None
        
        with self.current_port_lock:
            func = getattr(self.current_port, name)
            if args:
                return func(**args)
            return func()

    def get_port_info(self, specific : List[str]=None) -> Dict[str, Any] | None:
        ''' Returns dict with specific information about the port. '''

        if not self.current_port:
            return None

        with self.current_port_lock:
            info = {}
            for x in specific:
                try:
                    info[x] = getattr(self.current_port, x)
                except AttributeError as e:
                    print(f"ERROR in get_port_info(): Attribute not found: {x}, omitting.")
            return info

    def get_port_attribute(self, name : str) -> Any:
        if self.current_port:
            with self.current_port_lock:
                return getattr(self.current_port, name)

    def get_dsr(self):
        with self.current_port_lock:
            return self.current_port.dsr if self.current_port and self.current_port.is_open else False

    def get_cts(self):
        with self.current_port_lock:
            return self.current_port.cts if self.current_port and self.current_port.is_open else False

    def read_until(self, expected : bytes, size=None):
        with self.current_port_lock:
            return self.current_port.read_until(expected, size)

    def reset_input_buffer(self):
        with self.current_port_lock:
            self.current_port.reset_input_buffer()

    def set_write_timeout(self, timeout : int):
        with self.current_port_lock:
            if self.current_port_lock:
                self.current_port.write_timeout = timeout

    # ---------------- Internal Port Operations ---------------- #

    def _listen_on_port(self, func : callable):
        ''' 
        Body of the listenning thread.
    
        Args:
        - body (callable) : Invoked during each iteration of the threads mainloop.
        '''
        while True:
            if self.current_port and self.current_port.is_open:
                with self.current_port_lock:
                    func()
            else:
                sleep(1.0)