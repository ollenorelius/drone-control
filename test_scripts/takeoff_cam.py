import dronekit as dk
import sys
import time
from logger import Logger
import state_machines as sm
import utils as u

conn_number = 0
if len(sys.argv) != 1:
    try:
        conn_number = int(sys.argv[1])
    except:
        conn_number = 0
baudrate = 57600
port = '/dev/ttyS%s'%conn_number #If using hardware serial. HW serial has issues relating to GPU throttling (google it), use with caution
port = '/dev/ttyACM%s'%conn_number #If using USB. Safe but physically clunky.
print 'Connecting to %s at %s baud'%(port, baudrate)
vehicle = dk.connect(port, wait_ready=True, baud=baudrate)

print('Connected!')
print('Battery voltage is %f V'%vehicle.battery.voltage)
fly_sm = sm.Flyer(vehicle)
cam_sm = sm.CameraHandler()
main_state = 0
main_timer = 0

while main_state != 100:
    main_state = fly_sm.run()
    cam_sm.run()
    positions = u.get_relative_target_coords(vehicle, cam_sm.coords)
    for p in positions: print(p)

cam_sm.close()
