import dronekit as dk
import sys
import time

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


for i in range(100):
    time.sleep(0.1)
    yaw = vehicle.attitude.yaw
    loc = vehicle.location.local_frame
    print("Coordinates: %s, Yaw: %s\r"%(loc,yaw))

print 'Landing!'
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
