from utils import ModbusMode

class AppState:
    ''' 
    Holds the application state.
    
    Fields:

    - modbus_on   (bool)       : Determines if modbus protocol is used or if normal serial transmission is used.
    - modbus_mode (ModbusMode) : Specifies modbus mode (slave, master, etc)
    '''
    def __init__(self):
        self.modbus_on              = False
        self.modbus_mode            = ModbusMode.MASTER
        self.modbus_slave_addr      = 1 # Addr assigned to unit when in slave mode
        self.modbus_tr_timeout      = 100
        self.modbus_retransmissions = 1
        self.modbus_target_addr     = 0
        self.modbus_command         = 1