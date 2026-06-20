import os
from typing import Dict


class Menu:
    def __init__(self, options : Dict[str, callable]):
        self._options = list(options.keys()) + ["Exit"]
        self._functions = list(options.values()) + [self.exit]
        self._repeat = True

    def exit(self):
        print("Exiting menu.")
        self._repeat = False

    def show(self):
        ''' Prints list of avaialable options in format: N. Option description.'''
        for i, option in enumerate(self._options):
            print(f"{i}. {option}")

    def validate_input(self, user_input : str):
        ''' Validates user input for option selection. '''
        try:
            i = int(user_input.strip())
        except Exception as e:
            return False
        
        return i >= 0 and i < self.length()

    def length(self):
        return len(self._options)

    def loop(self):
        ''' Main loop takes user input, validates it and runs chosen command. '''

        while self._repeat:
            self.show()
            i = input()

            os.system("cls" if os.name == "nt" else "clear")

            if self.validate_input(i):
                print("Input valid executing")
                option_idx = int(i.strip())
                self._functions[option_idx]()
