from typing import List
from serial.tools.list_ports_common import ListPortInfo

class ListPortInfoWrapper(ListPortInfo):
    ''' Wraps ListPortInfo from serial.tools.list_ports_common. 
    
    Attributes:

    FIELDS : Tuple of all fields.
    _valid_fields : FIELDS converted to set.
    _info : Dictionary, keys are names of attributes, values are attributes values from the super class.

    '''
    FIELDS = (
        "device",
        "name",
        "description",
        "hwid",
        "vid",
        "pid",
        "serial_number",
        "location",
        "manufacturer",
        "product",
        "interface"
    )

    def __init__(self, info : ListPortInfo):
        super().__init__(info.device)

        self._valid_fields = set(self.FIELDS)
        self._info = dict()

        for field in self.FIELDS:
            val = getattr(info, field)
            setattr(self, field, val)
            self._info[field] = val

    def print_info(self, options : List[str] = None):
        ''' Prints info about the port. 

        options : List of specific attributes to print. 
                  If not specified, all attributes will be printed.

        '''

        if options:
            given = set(options)

            if given.issubset(self._valid_fields):
                for option in options:
                    print(f"{option} : {self._info[option]}")
            else:
                wrong = given.difference(self._valid_fields)
                print(f"ERROR in print_info: {wrong}")
        else:
            for key, val in self._info.items():
                print(f"{key} : {val}")
