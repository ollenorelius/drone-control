import time
import dronekit as dk
from logger import Logger
import socket
import struct
import sys
import io
import utils as u
from bbox import BoundingBox

class CameraHandler(object):
    """State machine to handle communications with the Neural net server.
    Basically listens on a port for centers being sent"""
    connection = None
    client_socket = None
    stream = io.BytesIO()
    centers = []
    state = 0
    data_stream = io.BytesIO()

    def box_to_center(self, bboxes):
        centers = []
        for box in bboxes:
            x = (box.coords[0] + box.coords[2])/2
            y = (box.coords[1] + box.coords[3])/2
            centers.append((x,y))
        return centers

    def __init__(self):
        self.client_socket = socket.socket()
        self.client_socket.connect(('biffen.local', 8001))
        print 'Connected to NN server!'
        # Make a file-like object out of the connection
        self.connection = self.client_socket.makefile('rwb')

    def run(self):
        self.centers = []
        bboxes = []

        self.connection.write(struct.pack('<c', b'd'))
        self.connection.flush() #Send b'c' to NNServer to request data

        box_count = struct.unpack('<L', self.connection.read(struct.calcsize('<L')))[0]
        self.data_stream.seek(0)

        for i in range(box_count):
            data = struct.unpack('<ffffff', self.connection.read(struct.calcsize('<ffffff')))
            coords = (data[0], data[1], data[2], data[3])
            classification = data[4]
            confidence = data[5]
            bboxes.append(BoundingBox(coords, confidence, classification))
        self.data_stream.seek(0)

        self.centers = self.box_to_center(bboxes)

        '''except:
            print('Connection failed! E:(%s)'%sys.exc_info()[0])
            print(sys.exc_info()[1])
            print(sys.exc_info()[2])
            self.connection.close()
            self.client_socket.close()
            self.state = -1'''
    def close(self):
        self.connection.close()
        self.client_socket.close()


class Takeoff():
    '''
    State machine to control flight plan.
    '''
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
            #print 'Mode: %s, Armed = %s\r'%(self.vehicle.mode.name, self.vehicle.armed)
            if(self.vehicle.armed == True and self.vehicle.mode.name == self.mode):
                print 'Armed!'
                self.state = 100
                self.start_timer = t
        elif self.state == 100:
            if t - self.start_timer > 3: #Let drone arm for 3 seconds
                self.state = 2 #Then go to next state

        elif self.state == 2:
            print 'running simple takeoff'
            self.vehicle.simple_takeoff(1.4)
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
                self.state = 1000
                print 'Done.'

        elif self.state == 1000:
            print 'Program finished!'
            vehicle.close()
        return self.state


class Turn():
    '''
    State machine to control flight plan.
    '''
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
                self.state = 100
                self.start_timer = t

        elif self.state == 100:
            if t - self.start_timer > 3: #Let drone arm for 1 seconds
                self.state = 2 #Then go to next state

        elif self.state == 2:
            print 'running simple takeoff'
            self.vehicle.simple_takeoff(1)
            self.start_timer = t
            self.state = 3

        elif self.state == 3:
            if t - self.start_timer > 3: #Let drone take off for 3 seconds
                self.state = 4 #Then go to next state
                self.vehicle.mode = dk.VehicleMode('GUIDED')

        elif self.state == 4:
            if self.vehicle.mode.name == 'GUIDED':
                self.log = Logger() # Init logger
                self.log.write_line('N\tE\tD\tY\n')
                self.start_timer = t
                print 'Sent rotate command!'

                u.condition_yaw(self.vehicle, -90, relative=True)
                #self.vehicle.mode = dk.VehicleMode(self.mode)
                self.state = 5

        elif self.state == 5:
            yaw = self.vehicle.attitude.yaw
            loc = self.vehicle.location.local_frame
            h = self.vehicle.rangefinder.distance
            #print dir(self.vehicle.location)
            #print("Coordinates: %.3f N, %.3f E, %.3f D Yaw: %3f\r"%(loc.north, loc.east, h ,yaw))
            self.log.write_line('%s\t%s\t%s\t%s\n'%(loc.north, loc.east, h, yaw))
            if t - self.start_timer > 20: #Fly for x secs
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
                self.state = 1000
                print 'Done.'

        elif self.state == 1000:
            print 'Program finished!'
            vehicle.close()
        return self.state



class Turn():
    '''
    State machine to control flight plan.
    '''
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
                self.state = 100
                self.start_timer = t

        elif self.state == 100:
            if t - self.start_timer > 3: #Let drone arm for 1 seconds
                self.state = 2 #Then go to next state

        elif self.state == 2:
            print 'running simple takeoff'
            self.vehicle.simple_takeoff(1)
            self.start_timer = t
            self.state = 3

        elif self.state == 3:
            if t - self.start_timer > 3: #Let drone take off for 3 seconds
                self.state = 4 #Then go to next state
                self.vehicle.mode = dk.VehicleMode('GUIDED')

        elif self.state == 4:
            if self.vehicle.mode.name == 'GUIDED':
                self.log = Logger() # Init logger
                self.log.write_line('N\tE\tD\tY\n')
                self.start_timer = t
                print 'Sent rotate command!'
                start_N = self.vehicle.location.local_frame.north
                start_E = self.vehicle.location.local_frame.east

                u.send_ned_target(self.vehicle, start_N + 0.93, start_E - 0.34, 1)
                #self.vehicle.mode = dk.VehicleMode(self.mode)
                self.state = 5

        elif self.state == 5:
            yaw = self.vehicle.attitude.yaw
            loc = self.vehicle.location.local_frame
            h = self.vehicle.rangefinder.distance
            #print dir(self.vehicle.location)
            #print("Coordinates: %.3f N, %.3f E, %.3f D Yaw: %3f\r"%(loc.north, loc.east, h ,yaw))
            self.log.write_line('%s\t%s\t%s\t%s\n'%(loc.north, loc.east, h, yaw))
            if t - self.start_timer > 20: #Fly for x secs
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
                self.state = 1000
                print 'Done.'

        elif self.state == 1000:
            print 'Program finished!'
            vehicle.close()
        return self.state

class Seek():
    '''
    State machine to control flight plan.
    '''
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
            #print 'Mode: %s, Armed = %s\r'%(self.vehicle.mode.name, self.vehicle.armed)
            if(self.vehicle.armed == True and self.vehicle.mode.name == self.mode):
                print 'Armed!'
                self.state = 100
                self.start_timer = t
        elif self.state == 100:
            if t - self.start_timer > 3: #Let drone arm for 3 seconds
                self.state = 2 #Then go to next state

        elif self.state == 2:
            print 'running simple takeoff'
            self.vehicle.simple_takeoff(1)
            self.start_timer = t
            self.state = 3

        elif self.state == 3:
            if t - self.start_timer > 3: #Let drone take off for 3 seconds
                self.state = 4 #Then go to next state
                self.vehicle.mode = dk.VehicleMode('GUIDED')

        elif self.state == 4:
            if self.vehicle.mode.name == 'GUIDED':
                self.log = Logger() # Init logger
                self.log.write_line('N\tE\tD\tY\n')
                self.start_timer = t
                print 'Sent rotate command!'

                u.condition_yaw(self.vehicle, heading=-90, rate=20, relative=False)
                self.state = 401

        elif self.state == 401:
            print dir(self.vehicle.location)
            yaw = self.vehicle.attitude.yaw
            loc = self.vehicle.location.local_frame
            h = self.vehicle.rangefinder.distance
            self.log.write_line('%s\t%s\t%s\t%s\n'%(loc.north, loc.east, h, yaw))
            if t - self.start_timer > 5: #rotate for 5 secs
                self.state = 402

        elif self.state == 402:
            if self.vehicle.mode.name == 'GUIDED':
                self.log = Logger() # Init logger
                self.log.write_line('N\tE\tD\tY\n')
                self.start_timer = t
                print 'Sent rotate command!'

                u.condition_yaw(self.vehicle, heading=90, rate=20, relative=False)
                self.state = 403

        elif self.state == 403:
            yaw = self.vehicle.attitude.yaw
            loc = self.vehicle.location.local_frame
            h = self.vehicle.rangefinder.distance
            self.log.write_line('%s\t%s\t%s\t%s\n'%(loc.north, loc.east, h, yaw))
            if t - self.start_timer > 10: #rotate for 10 secs
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
                self.state = 1000
                print 'Done.'

        elif self.state == 1000:
            print 'Program finished!'
            vehicle.close()
        return self.state
