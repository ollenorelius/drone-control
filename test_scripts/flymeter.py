import dronekit as dk
import sys
import time
from logger import Logger
import utils as u
import math

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

print 'Waiting to arm...'
mode = 'POSHOLD'
vehicle.mode = dk.VehicleMode(mode)

print 'Mode: %s'%vehicle.mode.name
vehicle.armed = True
time.sleep(0.1)
while(vehicle.armed == False and vehicle.mode.name != mode):
    print 'Mode: %s, Armed = %s\r'%(vehicle.mode.name, vehicle.armed)
    time.sleep(0.2)
print 'Armed!'
time.sleep(2)

print 'running simple takeoff'
vehicle.simple_takeoff(1)

log = Logger()
log.write_line('N\tE\tD\tY\n')
n_time = 100
d_time = 0.1
loc = vehicle.location.local_frame
h_n = loc.north
h_e = loc.east
h_d = loc.down
home = dk.LocationLocal(h_n,h_e,h_d)
dest = dk.LocationLocal(h_n+1,h_e-0.3,h_d)
for i in range(n_time):
    time.sleep(d_time)
    yaw = vehicle.attitude.yaw
    loc = vehicle.location.local_frame
    N = loc.north
    E = loc.east
    D = vehicle.rangefinder.distance
    print("Coordinates: %.3f N, %.3f E, %.3f D Yaw: %3f\r"%(N, E, D ,yaw))
    log.write_line('%s\t%s\t%s\t%s\n'%(N, E, D, yaw))

    if i > 3/d_time:
        ang = 347
        r = 1
        vn = math.cos(ang*math.pi/180) * r
        ve = math.sin(ang*math.pi/180) * r
        print((vn, ve))
        u.send_ned_velocity(vehicle, vn, ve, 0)
        print 'moving!'

u.send_ned_velocity(vehicle,0,0,0)


print 'Landing!'
log.close()
while(vehicle.mode.name != 'LAND'):
    vehicle.mode = dk.VehicleMode('LAND')
    time.sleep(2)

time.sleep(4)

while(vehicle.mode.name != mode):
    print 'Mode: %s\r'%vehicle.mode.name
    vehicle.mode = dk.VehicleMode(mode)
    time.sleep(2)
print 'Mode: %s\r'%vehicle.mode.name
print 'Disarming'
vehicle.armed = False
while(vehicle.armed == True):
    vehicle.armed = False
    time.sleep(1)
print 'Done!'
vehicle.close()
