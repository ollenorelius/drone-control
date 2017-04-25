import time
import dronekit as dk
from logger import Logger
import socket
import struct
import sys
import io

class CameraHandler(object):
    """State machine to handle communications with the Neural net server.
    Basically listens on a port for centers being sent"""
    connection = None
    client_socket = None
    stream = io.BytesIO()
    centers = []
    def __init__(self):
        self.client_socket = socket.socket()
        self.client_socket.connect(('puff-buntu.local', 8001))

        # Make a file-like object out of the connection
        self.connection = self.client_socket.makefile('rwb')
    def run(self):
        try:
            box_count = struct.unpack('<L', self.connection.read(struct.calcsize('<L')))[0]
            for i in range(box_count):
                print i
                coord = struct.unpack('<ff', self.connection.read(struct.calcsize('<ff')))
                self.centers.append(coord)
                #print(coord)
        except:
            print('Connection failed! E:(%s)'%sys.exc_info()[0])
            self.connection.close()
            self.client_socket.close()
    def close(self):
        self.connection.close()
        self.client_socket.close()


class Flyer():
    state = 0
    start_timer = 0
    vehicle = None
    mode = 'POSHOLD'
    log = None

    def __init__(self, vehicle, state=0):
        self.vehicle = vehicle
        self.state = state

    def run(self):
        t = time.time()
        if self.state == 0:
            print 'Waiting to arm...'
            self.vehicle.mode = dk.VehicleMode(self.mode)

            print 'Mode: %s'%self.vehicle.mode.name
            self.vehicle.armed = True
            self.state = 1
        elif self.state == 1:
            print 'Mode: %s, Armed = %s\r'%(self.vehicle.mode.name, self.vehicle.armed)
            if(self.vehicle.armed == True and self.vehicle.mode.name == self.mode):
                print 'Armed!'
                self.state = 2
        elif self.state == 2:
            print 'running simple takeoff'
            self.vehicle.simple_takeoff(1)
            self.start_timer = t
            self.state = 3
        elif self.state == 3:
            if t - self.start_timer > 3: #Let drone take off for 3 seconds
                self.state = 4 #Then go to next state

        elif self.state == 4:
            self.log = Logger() # Init logger
            self.log.write_line('N\tE\tD\tY\n')
            self.start_timer = t
            self.state = 5

        elif self.state == 5:
            yaw = self.vehicle.attitude.yaw
            loc = self.vehicle.location.local_frame
            h = self.vehicle.rangefinder.distance
            #print("Coordinates: %.3f N, %.3f E, %.3f D Yaw: %3f\r"%(loc.north, loc.east, h ,yaw))
            self.log.write_line('%s\t%s\t%s\t%s\n'%(loc.north, loc.east, h, yaw))
            if t - self.start_timer > 10: #Fly for x secs
                self.state = 6
                self.log.close()

        elif self.state == 6:
            #Mode is set after the check in order to guarantee that there is
            # one cycle between setting and checking.
            print 'Landing!'
            if self.vehicle.mode == dk.VehicleMode('LAND'):
                self.state = 7
                self.start_timer = t
            self.vehicle.mode = dk.VehicleMode('LAND')

        elif self.state == 7:
            if t - self.start_timer > 5:
                if self.vehicle.mode == dk.VehicleMode(self.mode):
                    print 'Reset to mode: %s\r'%self.vehicle.mode.name
                    self.state = 8
                self.vehicle.mode = dk.VehicleMode(self.mode)
        elif self.state == 8:
            print 'Disarming\r'
            self.vehicle.armed = False
            if self.vehicle.armed == False:
                self.state = 100
                print 'Done.'

        elif self.state == 100:
            print 'Program finished!'
            vehicle.close()
        return self.state
