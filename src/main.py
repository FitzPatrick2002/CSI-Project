from App import App

# MODBUS NOTES
# - Physical, data link, application layer

# MODBUS (ASCII)
# 1. Slave / Master mode
# 2. Generate ID?
# 3. Identify possible commands
# 4. Message format
#    - Query     :
#    - Response  :
#    - Broadcast : 
# 5. UI
#    - ModbusMode button
#    - Query      button
#    - Broadcast  button
#    - 

app = App()

if __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt as k:
        print(f"Keyboard interrupt, exiting")