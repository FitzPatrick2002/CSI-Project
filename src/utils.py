from enum import Enum
import tkinter as tk
from tkinter import ttk

def get_lrc(message : bytes):
    '''
    Computes lrc for the given message. 
    Args:
        - message (str) : Message for which lrc is evaluated.
    '''
    lrc = sum(message)
    lrc = (-lrc) & 0xFF
    return lrc

def set_widget_state(obj : tk.Widget, 
                     mode : any, 
                     active : any,
                     when_active : str=tk.NORMAL,
                     when_not_active : str=tk.DISABLED): 
    if mode == active:
        obj.configure(state=when_active)
    else:
        obj.configure(state=when_not_active)

def toggle_widget(obj : tk.Widget | ttk.Widget):
    ''' Toggles the widget state between "disabled" and "enabled".'''
    state_map = {
        "normal" : "disabled",
        "disabled" : "normal"
    }
    
    state = str(obj.cget("state"))

    if state in state_map.keys():
        obj.config(state=state_map[state])

def prepare_modbus_ascii_message(address : int, command : int, data : str) -> bytes:
    ''' 
    Constructs and ASCII mode message and sends via self.current_port. 
    Mesage format: [:][addres - 2 chars][command - 2 chars][data - N chars][LRC - 2 chars][CR-LF - 2 chars]
    
    Args:
        - address (int) : Address of the slave.
        - command (int) : Command code.
        - data    (str) : Payload of the command. 

    Returns:
        - (bytes)       : Message formatted according to the pattern above. 
    '''

    print("formulatiing message")

    colon   = ":".encode("ascii")
    address = f"{address:02X}".encode("ascii")
    command = f"{command:02X}".encode("ascii")
    data    = data.encode("ascii")
    lrc     = get_lrc(address + command + data)
    lrc     = f"{rlc}:02X".encode('ascii')
    term = "\r\n".encode("ascii")

    message = colon + address + command + data + lrc + term

    return message

def get_modbus_ascii_message_address(message : str):
    return message [1 : 3]

def get_modbus_ascii_message_command(message : str):
    return message [3 : 5]

def get_modbus_ascii_message_data(message : str):
    '''
    Removes all formatting from MODBUS ascii message and returns only the payload.
    Mesage format: [:][addres - 2 chars][command - 2 chars][data - N chars][LRC - 2 chars][CR-LF - 2 chars]
    '''
    return message[5 : -4]

def get_modbus_ascii_message_lrc(message : str):
    return message [3 : 5]

status_colors = {False : "Red", True : "Green"}

terminator_map = {
    "CR" : "\n",
    "LF" : "\r",
    "CR-LF" : "\r\n"
}

class Consts():
    PING_REQ  = "__PING_REQ__"
    PING_RESP = "__PING_RESP__"

class ModbusMode(Enum):
    MASTER = "master"
    SLAVE  = "slave"

ModbusMode.ALL = [i.value for i in ModbusMode] 
