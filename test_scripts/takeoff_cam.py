import dronekit as dk
import sys
import time
from logger import Logger
import state_machines as sm
import utils as u
from logger import Logger

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
l = Logger(name=None, folder=car_coords)
while (main_state != 100) & (cam_sm.state != -1):
    main_state = fly_sm.run()
    cam_sm.run()
    positions = u.get_relative_target_coords(vehicle, cam_sm.centers)
    global_pos = u.get_global_target_coords(vehicle, cam_sm.centers)
    for p in global_pos:
        print 'car is at (%.2f,%.2f)'%p
        l.write_line('%s\t%s'%p)

l.close()
cam_sm.close()
