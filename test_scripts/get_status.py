import dronekit as dk

veh = dk.connect('/dev/ttyACM0', wait_ready=True)

print('Connected!')
print('Battery voltage: %f'%veh.battery.voltage)
