import dronekit as dk
import sys
import time
from pymavlink import mavutil

def condition_yaw(heading, relative=False):
    if relative:
        is_relative=1 #yaw relative to direction of travel
    else:
        is_relative=0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

conn_number = 0
if len(sys.argv) != 1:
    try:
        conn_number = int(sys.argv[1])
    except:
        conn_number = 0
baudrate = 115200
port = '/dev/ttyS%s'%conn_number
print 'Connecting to %s at %s baud'%(port, baudrate)
vehicle = dk.connect(port, wait_ready=True, baud=baudrate)

print('Connected!')
print('Battery voltage is %f V'%vehicle.battery.voltage)

print 'Waiting to arm...'
mode = 'POSHOLD'
vehicle.mode = dk.VehicleMode(mode)

print 'Mode: %s'%vehicle.mode.name
vehicle.armed = True
while(vehicle.armed == False and vehicle.mode.name != mode):
    print 'Mode: %s\r'%vehicle.mode.name
    vehicle.mode = dk.VehicleMode(mode)
    vehicle.armed = True
print 'Armed!'
time.sleep(2)

print 'running simple takeoff'
vehicle.simple_takeoff(1)

time.sleep(6)
print 'Turning!'
condition_yaw(90, relative=True)

time.sleep(4)

print 'Landing!'
while(vehicle.mode.name != 'LAND'):
    vehicle.mode = dk.VehicleMode('LAND')

print 'Disarming'
while(vehicle.armed == True):
    vehicle.armed = False
print 'Done!'
vehicle.close()
