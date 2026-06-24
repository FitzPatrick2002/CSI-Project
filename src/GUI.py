import tkinter as tk
from tkinter import ttk
from typing import Dict, List

import utils
from PortsRegistry import PortsRegistry
from ListPortInfoWrapper import ListPortInfoWrapper
import serial
from itertools import compress
import queue
import time
from utils import Consts
from enum import Enum
from utils import ModbusMode
from AppState import AppState

# TODO:
# - MODBUS:
# - (ok) - comm 1 - addr -> send from master to slave
# - (ok) - comm 1 - broadcast -> send from master to all slaves
# - (ok) comm 1 - Check if master can't receive random slave transmissions
# - comm 2 - addr -> Make sure that master can receive from the given slave
# - comm 2 - broadcast -> make sure master recevies does not display anything
# - Validate lrc

class ModbusPane(tk.LabelFrame):
    ''' Contains MODBUS configuration & settings. '''
    def __init__(self, app_state : AppState, ports_registry : PortsRegistry, master=None):
        tk.LabelFrame.__init__(self, master, text="MODBUS (ASCII)", labelanchor="nw")
        self.state = app_state
        self.registry = ports_registry
        self.create_widgets()

    def create_widgets(self):
        self.btn_toggle_modbus = tk.Button(self, text="MODBUS", command=self.toggle_modbus)
        self.btn_toggle_modbus.config(background=utils.status_colors[self.state.modbus_on])

        self.box_mode_l = tk.Label(self, text="Mode")
        self.box_mode_w = ttk.Combobox(self, values=ModbusMode.ALL, state=tk.DISABLED)
        self.box_mode_w.bind("<<ComboboxSelected>>", self.set_mode)

        # Applies only if in slave mode
        possible_addr = [i for i in range(1, 248)]
        self.box_addr_l = tk.Label(self, text="Address")
        self.box_addr_w = ttk.Combobox(self, values=possible_addr, state=tk.DISABLED)
        self.box_addr_w.bind("<<ComboboxSelected>>", self.set_addr)

        possible_timeouts = [i for i in range(100, 10**4+1, 100)]
        self.box_tr_timeout_l = tk.Label(self, text="Timeout [ms]")
        self.box_tr_timeout_w = ttk.Combobox(self, values=possible_timeouts, state=tk.DISABLED)
        self.box_tr_timeout_w.bind("<<ComboboxSelected>>", self.set_timeout)

        possible_timeouts = [i for i in range(0, 10**3+1, 10)]
        self.box_frame_timeout_l = tk.Label(self, text="Frame Timeout [ms]")
        self.box_frame_timeout_w = ttk.Combobox(self, values=possible_timeouts, state=tk.DISABLED)
        self.box_frame_timeout_w.bind("<<ComboboxSelected>>", self.set_frame_timeout)

        possible_retransmission = [i for i in range(6)]
        self.box_retransmission_l = tk.Label(self, text="Retransmissions")
        self.box_retransmission_w = ttk.Combobox(self, values=possible_retransmission, state=tk.DISABLED)
        self.box_retransmission_w.bind("<<ComboboxSelected>>", self.set_retransmissions)

        possible_target_addr = [i for i in range(1, 248)]
        possible_target_addr.insert(0, "broadcast")
        self.box_target_l = tk.Label(self, text="Target Addr")
        self.box_target_w = ttk.Combobox(self, values=possible_target_addr, state=tk.DISABLED)
        self.box_target_w.bind("<<ComboboxSelected>>", self.select_target)

        possible_commands = [1, 2]
        self.box_command_l = tk.Label(self, text="Command")
        self.box_command_w = ttk.Combobox(self, values=possible_commands, state=tk.DISABLED)
        self.box_command_w.bind("<<ComboboxSelected>>", self.set_command)

        self.btn_toggle_modbus.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E)

        self.box_mode_l.grid(row=1, column=0, sticky=tk.W)
        self.box_mode_w.grid(row=1, column=1, sticky=tk.W)

        self.box_addr_l.grid(row=2, column=0, sticky=tk.W)
        self.box_addr_w.grid(row=2, column=1, sticky=tk.W)

        self.box_tr_timeout_l.grid(row=3, column=0, sticky=tk.W)
        self.box_tr_timeout_w.grid(row=3, column=1, sticky=tk.W)

        self.box_frame_timeout_l.grid(row=4, column=0, sticky=tk.W)
        self.box_frame_timeout_w.grid(row=4, column=1, sticky=tk.W)

        self.box_retransmission_l.grid(row=5, column=0, sticky=tk.W)
        self.box_retransmission_w.grid(row=5, column=1, sticky=tk.W)

        self.box_target_l.grid(row=6, column=0, sticky=tk.W)
        self.box_target_w.grid(row=6, column=1, sticky=tk.W)

        self.box_command_l.grid(row=7, column=0, sticky=tk.W)
        self.box_command_w.grid(row=7, column=1, sticky=tk.W)

    # ----------- UI CALLBACKS ----------- #

    def toggle_modbus(self):
        self.state.modbus_on = not self.state.modbus_on
        self.btn_toggle_modbus["bg"] = utils.status_colors[self.state.modbus_on]

        self.set_modbus_widgets_visible(self.state.modbus_on)

    def set_timeout(self, ev : tk.Event):
        timeout = int(self.box_tr_timeout_w.get())
        self.state.modbus_timeout = timeout
        self.registry.set_write_timeout(timeout)

    def set_frame_timeout(self, ev : tk.Event):
        self.state.frame_timeout = int(self.box_frame_timeout_w.get())
     
    def set_mode(self, ev : tk.Event):
        ''' Sets the mode of the device in modbus system & disables / enables appropriate configuration widgets. '''
        self.state.modbus_mode = ModbusMode(self.box_mode_w.get())
        #utils.toggle_widget(self.box_addr_w)

        utils.set_widget_state(self.box_tr_timeout_w, self.state.modbus_mode, ModbusMode.MASTER, when_active="readonly")
        self.box_frame_timeout_w.config(state="readonly")
        #utils.set_widget_state(self.box_frame_timeout_w, self.state.modbus_mode, ModbusMode.SLAVE, when_active="readonly")
        #utils.set_widget_state(self.box_frame_timeout_w, self.state.modbus_mode, ModbusMode.MASTER, when_active="readonly")
        utils.set_widget_state(self.box_retransmission_w, self.state.modbus_mode, ModbusMode.MASTER, when_active="readonly")

        utils.set_widget_state(self.box_addr_w, self.state.modbus_mode, ModbusMode.SLAVE, when_active="readonly")
        utils.set_widget_state(self.box_target_w, self.state.modbus_mode, ModbusMode.MASTER, when_active="readonly")
        utils.set_widget_state(self.box_command_w, self.state.modbus_mode, ModbusMode.MASTER, when_active="readonly")

    def set_addr(self, ev : tk.Event):
        ''' Sets the device address when in slave mode. '''
        self.state.modbus_slave_addr = int(self.box_addr_w.get())
        print(self.state.modbus_slave_addr)

    def set_retransmissions(self, ev : tk.Event):
        self.state.modbus_retransmissions = int(self.box_retransmission_w.get())

    def select_target(self, ev : tk.Event):
        target = self.box_target_w.get()
        if target == 'broadcast':
            self.state.modbus_target_addr = 0 #'broadcast'
        else:
            self.state.modbus_target_addr = int(target)

    def set_command(self, ev : tk.Event):
        self.state.modbus_command = int(self.box_command_w.get())

    # ----------- ? ----------- #

    def set_modbus_widgets_visible(self, on):
        ''' 
        If the modbus mode is disabled, disables all modbus config options and enables the mode combobox if it's enabled.
        '''
        if on:
            self.box_mode_w.config(state=tk.NORMAL)
        else:
            self.box_mode_w.config(state=tk.DISABLED)
            self.box_addr_w.config(state=tk.DISABLED)
            self.box_tr_timeout_w.config(state=tk.DISABLED)
            self.box_frame_timeout_w.config(state=tk.DISABLED)
            self.box_retransmission_w.config(state=tk.DISABLED)
            self.box_target_w.config(state=tk.DISABLED)
            self.box_command_w.config(state=tk.DISABLED)

class RightPane(tk.LabelFrame):
    ''' Contains info & config of the selected COM port + DTR/DSR diagnosis. '''
    def __init__(self, app_state : AppState, ports_registry : PortsRegistry, master=None):
        tk.LabelFrame.__init__(self, master, text="Communication", labelanchor="nw")
        self.state = app_state
        self.registry = ports_registry
        self.create_widgets()

    def create_widgets(self):
        # 0. Define widgets

        # COM selection

        self.box_comports_l = tk.Label(self, text="COM PORT")
        self.box_comports_w = ttk.Combobox(self, values=["COM1", "COM2", "COM3"], postcommand=self.refresh_comports)
        self.box_comports_w.bind("<<ComboboxSelected>>", self.select_comport)

        # Bauds

        self.bit_rate_l = tk.Label(self, text="Bit Rate")
        self.bit_rate_w = tk.Text(self, width=7, height=1)

        # PDU 

        self.bytesize_l = tk.Label(self, text="Bytesize")
        self.bytesize_w = ttk.Combobox(self, values=serial.Serial.BYTESIZES)

        self.parity_l = tk.Label(self, text="Parity")
        self.parity_w = ttk.Combobox(self, values=serial.Serial.PARITIES)

        self.stopbits_l = tk.Label(self, text="Stopbits")
        self.stopbits_w = ttk.Combobox(self, values=serial.Serial.STOPBITS)

        # Flow control

        self.flow_ctrl_l = tk.Label(self, text="Flow Control")
        self.flow_ctrl_w = ttk.Combobox(self, values=["None", "xonxoff", "rtscts", "dsrdtr"])

        # Terminator

        vterm = (self.register(self.validate_terminator), "%P")
        self.terminator_w = ttk.Combobox(self, values=["", "CR", "LF", "CR-LF"], validatecommand=vterm, validate="key")
        self.terminator_l = tk.Label(self, text="Terminator")

        self.btn_apply_config_w = tk.Button(self, text="Apply", command=self.apply_com_config)

        # Set to 1 -> green, 0 -> red        
        self.btn_dtr = tk.Button(self, text="DTR : 0", bg="red", command=self.toggle_dtr)
        self.btn_rts = tk.Button(self, text="RTS : 0", bg="red", command=self.toggle_rts)
        self.status_colors = {False : "red", True : "green"}

        # Manual monitorin happens on separate thread, 1 -> green, 0 -> red
        self.dsr_monitor = tk.Label(self, text="DSR : 0", bg="red")
        self.cts_monitor = tk.Label(self, text="CTS : 0", bg="red")
        self.btn_monitor = tk.Button(self, text="Monitor", command=self.toggle_dsrcts_monitor)
        self.dtrcts_monitor_run = False
        
        # 1. Position widgets 

        self.box_comports_l.grid(row=0, column=0, sticky=tk.W)
        self.box_comports_w.grid(row=0, column=1, sticky=tk.W)

        self.bit_rate_l.grid(row=1, column=0, sticky=tk.W)
        self.bit_rate_w.grid(row=1, column=1, sticky=tk.W)

        self.bytesize_l.grid(row=2, column=0, sticky=tk.W)
        self.bytesize_w.grid(row=2, column=1, sticky=tk.W)

        self.parity_l.grid(row=3, column=0, sticky=tk.W)
        self.parity_w.grid(row=3, column=1, sticky=tk.W)
        
        self.stopbits_l.grid(row=4, column=0, sticky=tk.W)
        self.stopbits_w.grid(row=4, column=1, sticky=tk.W)

        self.flow_ctrl_l.grid(row=5, column=0, sticky=tk.W)
        self.flow_ctrl_w.grid(row=5, column=1, sticky=tk.W)

        self.terminator_l.grid(row=6, column=0, sticky=tk.W)
        self.terminator_w.grid(row=6, column=1, sticky=tk.W)

        self.btn_apply_config_w.grid(row=7, column=1, sticky=tk.N + tk.S + tk.E + tk.W)

        self.btn_dtr.grid(row=8, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.btn_rts.grid(row=8, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
        
        self.dsr_monitor.grid(row=9, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.cts_monitor.grid(row=9, column=1, sticky=tk.N + tk.S + tk.E + tk.W)
        self.btn_monitor.grid(row=10, column=0, columnspan=2, sticky=tk.N + tk.S + tk.E + tk.W)

    # ------------ Validation ------------ #

    def validate_terminator(self, text):
        return len(text) <= 2

    # ------------ Commands ------------ #

    def refresh_comports(self):
        ''' Refreshes the list of COM ports in the combobox. '''
        self.registry.refresh()
        self.box_comports_w['values'] = self.registry.get_ports_names()

    def select_comport(self, ev):
        ''' Selects com port & update the stats on the right with current port config. '''
        # 0. Select port

        port_name = self.box_comports_w.get()
        self.registry.open_port(port_name)

        port_data = self.registry.get_port_info([
            "name", "baudrate", "bytesize", "parity", "stopbits", "xonxoff", "rtscts", "dsrdtr"
        ])

        # 1. Update stats in GUI
        
        if port_name:

            self.bit_rate_w.delete(index1="1.0", index2="end-1c")
            self.bit_rate_w.insert(index="1.0", chars=str(port_data["baudrate"]))
            
            # Set the PDU
            self.bytesize_w.set(port_data["bytesize"])
            self.parity_w.set(port_data["parity"])
            self.stopbits_w.set(port_data["stopbits"])

            # Flow Control

            # Create a bit filter & extract the current value, order matters!
            flow_status = [
                not (port_data["xonxoff"] or port_data["rtscts"] or port_data["dsrdtr"]),
                port_data["xonxoff"], port_data["rtscts"], port_data["dsrdtr"]
            ]
            selected = list(compress(self.flow_ctrl_w['values'], flow_status))[0]
            self.flow_ctrl_w.set(selected)

    def apply_com_config(self):
        ''' Applies the config from GUI to selected COM. '''

        if self.registry.is_port_open():
            config = self.registry.apply_method_on_port("get_settings")

            config["baudrate"] = self.bit_rate_w.get(index1="1.0", index2="end-1c")
            config["bytesize"] = int(self.bytesize_w.get())
            config["parity"]   = self.parity_w.get()
            config["stopbits"] = float(self.stopbits_w.get())

            flow_type = self.flow_ctrl_w.get()
            if flow_type != "None":
                config["rtscts"] = config["xonxoff"] = config["dsrdtr"] = False
                config[flow_type] = True

            self.registry.apply_method_on_port("apply_settings", {"d" : config})

            selected_terminator = self.terminator_w.get()
            self.registry.terminator = utils.terminator_map.get(selected_terminator, selected_terminator)

    def toggle_dsrcts_monitor(self):
        self.dtrcts_monitor_run = not self.dtrcts_monitor_run
        self.monitor_dsrcts()

    def toggle_dtr(self):
        ''' Sets the dtr line to the opposite state than it currently is. '''
        self.registry.toggle_dtr()
        self.btn_dtr["bg"] = self.status_colors[self.registry.get_port_attribute("dtr")]

    def toggle_rts(self):
        ''' Sets the rts line to the opposite state than it currently is. '''
        self.registry.toggle_rts()
        self.btn_rts["bg"] = self.status_colors[self.registry.get_port_attribute("rts")]

    # ------------ Routines ------------ #

    def monitor_dsrcts(self):
        if self.dtrcts_monitor_run:
            print("Monitoring")

            self.dsr_monitor["bg"] = self.status_colors[self.registry.get_dsr()]
            self.dsr_monitor["text"] = f"DSR : {self.registry.get_dsr()}"
            self.cts_monitor["bg"] = self.status_colors[self.registry.get_cts()]
            self.cts_monitor["text"] = f"CTS : {self.registry.get_cts()}"
        
            self.btn_monitor.after(ms="1", func=self.monitor_dsrcts)

class LeftPane(tk.LabelFrame):
    ''' Contains Send & receive text fields & buttons for sending & pinging. '''

    def __init__(self, app_state : AppState, ports_registry : PortsRegistry, master=None):
        tk.LabelFrame.__init__(self, master, text="Port Configuration", labelanchor="nw")
        self.state = app_state
        self.registry = ports_registry
        self.create_widgets()

        self.output_box_queue = queue.Queue()
        self.ping_queue = queue.Queue()

    def create_widgets(self):

        # ----------------- LEFT ----------------- #

        # 2. Input window
        self.text_input_l = tk.Label(self, text="Input")
        self.text_input_w = tk.Text(self, width=50, height=5)

        # 3. Output window
        self.text_output_l = tk.Label(self, text="Output")
        self.text_output_w = tk.Text(self, width=50, height=5)

        # 4. Send button
        self.btn_send = tk.Button(self, text="SEND", command=self.send_msg)

        self.btn_listen = tk.Button(self, text="LISTEN", bg="red", command=self.toggle_listen)
        self.status_color = {False : "red", True : "green"}
        self.listenning = False

        # 5. PING - takes control over the text_output, measures only ping responses
        self.btn_ping = tk.Button(self, text="PING", command=self.send_ping)
        
        self.text_output_w.after(ms=1, func=self.read_output_queue)

        # 6. Positioning
        self.text_input_l.grid(row=0, column=0, sticky=tk.W)
        self.text_input_w.grid(row=1, column=0, columnspan=3)
        self.btn_send.grid(row=2, column=2, sticky=tk.E + tk.W)

        self.text_output_l.grid(row=3, column=0, sticky=tk.W)
        self.text_output_w.grid(row=4, column=0, columnspan=3)
        self.btn_listen.grid(row=5, column=0, sticky=tk.E + tk.W)
        self.btn_ping.grid(row=5, column=2, sticky=tk.E + tk.W)

    def send_msg(self):
        # 0. Send text

        txt = self.text_input_w.get(index1="1.0", index2="end-1c")
        self.text_input_w.delete(index1="1.0", index2="end")

        if self.state.modbus_on:
            self.registry.send_modbus_ascii(address=self.state.modbus_target_addr,
                                            command=self.state.modbus_command,
                                            data=txt)
        else:
            self.registry.send_msg(txt)
        
       # txt += ports_registry.terminator

      #  print(f"Sending: {txt}")
       # bytes = ports_registry.apply_method_on_port("write", {"data" : txt.encode('utf-8')})
       # print(f"Bytes sent: {bytes}")

    def send_ping(self):
        #self.btn_ping['state'] = tk.DISABLED
        self.ping_start = time.perf_counter()
        self.registry.send_msg(Consts.PING_REQ)

    def toggle_listen(self):
        ''' Toggles the listenning on port. '''

        if not self.registry.is_port_open():
            print("No port is open, nothing to listen to")
            return

        # 0. Set button status

        self.listenning = not self.listenning
        self.btn_listen["bg"] = self.status_color[self.listenning]

        # 1. Thread body

        def update_output_box():
            encoding = "ascii" if self.state.modbus_on else "utf-8"

            raw_data = self.registry.apply_method_on_port("read_until", {"expected" : self.registry.terminator.encode(encoding)})
            print(raw_data)
            #line = raw_data.decode(encoding)
            #line = line.split(self.registry.terminator)

            if raw_data:
                line = raw_data.decode(encoding)
                self.output_box_queue.put(line)

        # 2. Launch / Join the listenning thread

        if self.listenning:
            self.registry.apply_method_on_port("reset_input_buffer")
            self.registry.start_listenning_on_port(func=update_output_box)
        else: 
            self.registry.stop_listenning_on_port()

    def read_output_queue(self):
            ''' Reads characters from output queue. Inserts them in the text_output_w widget.'''
            # 0. Empty the queue

            while not self.output_box_queue.empty():
                try:
                    line = self.output_box_queue.get()
                except queue.Empty:
                    break

                if not self.state.modbus_on:
                    line = line.removesuffix(self.registry.terminator.strip())
                    match line:
                        case Consts.PING_REQ:
                            self.registry.send_msg(Consts.PING_RESP)
                        case Consts.PING_RESP:
                            self.ping_end = time.perf_counter()
                            self.text_output_w.insert(index="end", chars=f"PING: {self.ping_end - self.ping_start} [s]" + "\n")
                        case _:
                            self.text_output_w.insert(index="end", chars=line + "\n")
                else:
                    match self.state.modbus_mode:
                        case ModbusMode.MASTER:
                            print(f"Received message: {line}")
                            if self.state.modbus_command == 2 and self.state.modbus_target_addr != 0:
                                data = utils.get_modbus_ascii_message_data(line)
                                self.text_output_w.insert(index="end", chars=data + "\n")
                        case ModbusMode.SLAVE:
                            addr = int(utils.get_modbus_ascii_message_address(line))
                            if addr == self.state.modbus_slave_addr or addr == 0:
                                comm = int(utils.get_modbus_ascii_message_command(line))
                                data = utils.get_modbus_ascii_message_data(line)

                                if comm == 1:
                                    self.text_output_w.insert(index="end", chars=data + "\n")
                                elif comm == 2:
                                    self.state.modbus_target_addr = self.state.modbus_slave_addr
                                    self.state.modbus_command = comm
                        case _:
                            print("Neither slave nor master")

            self.text_output_w.after(ms=1, func=self.read_output_queue)

class TkApp(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.pack()

        self.app_state = AppState()
        self.ports_registry = PortsRegistry(app_state=self.app_state)

        self.create_layout()

    def create_layout(self):
        self.left_pane = LeftPane(master=self, app_state=self.app_state, ports_registry=self.ports_registry)
        self.right_pane = RightPane(master=self, app_state=self.app_state, ports_registry=self.ports_registry)
        self.modbus_pane = ModbusPane(master=self, app_state=self.app_state, ports_registry=self.ports_registry)

        self.left_pane.pack(side=tk.LEFT, anchor="n")
        self.modbus_pane.pack(side=tk.RIGHT, anchor="n") # Otherwise gets stuck in between the panes :<
        self.right_pane.pack(side=tk.RIGHT, anchor="n")
        



