import dronekit as dk
import math
from pymavlink import mavutil

class BoundingBox(object):
    '''
    Struct to send info to the PIL front end.

    coords: 1x4 array of box coordinates. [x1, y1, x2, y2]
    confidence: confidence score for the box
    classification: numerical class given to box
    '''
    coords = [-1, -1, -1, -1]
    confidence = 0
    classification = -1

    def __init__(self, in_coords, in_gamma, in_class):
        self.coords = in_coords
        self.confidence = in_gamma
        self.classification = in_class

def condition_yaw(vehicle, heading, rate=20, relative=False):
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
        10,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

def send_ned_target(vehicle, n, e, d):
    '''
    Move vehicle in direction based on specified velocity vectors.
    '''
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        dk.mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000000, # type_mask (speed and position enabled)
        n, e, -d, # x, y, z positions
        0.5, 0.5, 0.5, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    vehicle.send_mavlink(msg)


def send_ned_velocity(vehicle, velocity_x, velocity_y, velocity_z):
    '''
    Move vehicle in direction based on specified velocity vectors.
    '''
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        dk.mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    vehicle.send_mavlink(msg)


def get_relative_target_coords(vehicle, centers):

    '''
    Transforms picture coordinates to local coordinate system.
    This assumes camera is mounted at 45 degrees to the vertical, but angle can
    be modified by cam_mount_angle.
    Input: vehicle: Vehicle object from DroneKit
    centers: list of coord tuples in [0,1] representing found objects in image
    '''

    pi = 3.14159265
    pitch = vehicle.attitude.pitch
    roll = vehicle.attitude.roll

    h = vehicle.rangefinder.distance * math.cos(roll) * math.cos(pitch)

    cam_mount_angle = pi/4
    cam_x_fov = 62.2*pi/180
    cam_y_fov = 48.8*pi/180
    positions = []
    for c in centers:
        phi_x = (c[0]-0.5)*cam_x_fov
        phi_y = -(c[1]-0.5)*cam_y_fov

        theta_y = pitch + cam_mount_angle + phi_y
        theta_x = phi_x


        y = math.tan(theta_y) * h
        r = math.sqrt(y**2+h**2)
        x = r * math.tan(theta_x)
        '''print('phi = %s,%s'%(phi_x, phi_y))
        print('pitch = %s, roll = %s'%(pitch, roll))
        print('theta = %s,%s'%(theta_x, theta_y))
        print('x,y,r,h = %s,%s,%s,%s'%(x,y,r,h))'''
        positions.append((x,y))
    return positions

def get_global_target_coords(vehicle, centers):
    '''
    Get coordinates of found objects in global space. Centered at home position,
    ie start location. In meters.
    '''
    rel_coords = get_relative_target_coords(vehicle, centers)

    Nd = vehicle.location.local_frame.north
    Ed = vehicle.location.local_frame.east
    yaw = vehicle.attitude.yaw
    global_coords = []
    for c in rel_coords:
        x = c[0]
        y = c[1]

        Er = x * math.cos(yaw) + y * math.sin(yaw)
        Nr = -x * math.sin(yaw) + y * math.cos(yaw)
        print(Nd)
        print(Nr)
        N = Nd + Nr
        E = Ed + Er

        global_coords.append((N,E))
    return global_coords
