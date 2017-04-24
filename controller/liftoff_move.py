import dronekit as dk
import sys
conn_number = 0
if len(sys.argv) != 1:
    try:
        conn_number = int(sys.argv[1])
    except:
        conn_number = 0

baudrate = 57600
port = '/dev/ttyS%s'%conn_number
print 'Connecting to %s at %s baud'%(port, baudrate)
veh = dk.connect(port, wait_ready=True, baud=baudrate)

print('Connected!')
print('Battery voltage is %f V'%veh.battery.voltage)

print 'Waiting for arm... ',
while not veh.armed:
    pass
print('OK')

veh.simple_takeoff(1)
