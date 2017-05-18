import dronekit as dk
import math
from pymavlink import mavutil
import struct
import sys

def set_home(vehicle, lat=1, lon=1,alt=-1):
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_DO_SET_HOME, #command
        0, #confirmation
        0,    # param 1, (1=use current location, 0=use specified location)
        0,          # param 2, unused
        0,          # param 3,unused
        0, # param 4, unused
        lat, lon, alt)    # param 5 ~ 7 latitude, longitude, altitude
    # send command to vehicle
    vehicle.send_mavlink(msg)

def condition_yaw(vehicle, heading, direction=1, rate=20, relative=False):
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
        rate,          # param 2, yaw speed deg/s
        direction,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)

def send_ned_target(vehicle, n=None, e=None, d=None):
    '''
    Move vehicle in direction based on specified velocity vectors.
    If a direction is left unspecified, keep current location in that dimension.

    NOTE: d is reversed in this function to give positive Z upwards.
    In dronekit and MAVLink, d goes down.
    Here, send_ned_target(d=1) will send the drone to 1m above home.
    '''
    if n == None:
        n=vehicle.location.local_frame.north
    if e == None:
        e=vehicle.location.local_frame.east
    if d == None:
        d=-vehicle.location.local_frame.down

    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        dk.mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000000, # type_mask (speed and position enabled)
        n, e, -d, # x, y, z positions
        0.1, 0.1, 0.1, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    vehicle.send_mavlink(msg)

def send_ned_target_rel(vehicle, n=0, e=0, d=0):
    '''
    Move vehicle in direction based on specified velocity vectors.
    If a direction is left unspecified, keep current location in that dimension.

    NOTE: d is reversed in this function to give positive Z upwards.
    In dronekit and MAVLink, d goes down.
    '''
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        dk.mavutil.mavlink.MAV_FRAME_BODY_NED, # frame
        0b0000111111000000, # type_mask (speed and position enabled)
        n, e, -d, # x, y, z positions
        0.1, 0.1, 0.1, # x, y, z velocity in m/s
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
    if vehicle.location.local_frame.north == None:
        print('In get_global_target_coords: Got local_frame.north == None!')
        global_coords = []
    else:
        #print dir(vehicle.location.local_frame)
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

def simple_move(vehicle, dir, dist=0.1):

    yaw = vehicle.attitude.yaw
    pos = vehicle.location.local_frame
    if(vehicle.location.local_frame.north == None):
        return -1
    if dir == 'w':
        N_dist = dist*math.sin(yaw)
        E_dist = dist*math.cos(yaw)
    elif dir == 's':
        N_dist = dist*math.sin(yaw+math.pi)
        E_dist = dist*math.cos(yaw+math.pi)
    elif dir == 'a':
        N_dist = dist*math.sin(yaw+math.pi/2)
        E_dist = dist*math.cos(yaw+math.pi/2)
    elif dir == 'd':
        N_dist = dist*math.sin(yaw+3*math.pi/2)
        E_dist = dist*math.cos(yaw+3*math.pi/2)
    else:
        print('Error: Invalid direction passed to simple_move: %s'%dir)
        return -1

    send_ned_target(vehicle, N_dist+pos.north, E_dist+pos.east)
    return 1

def simple_rel_move(vehicle, dir, dist=0.1):
    if(vehicle.location.local_frame.north == None):
        return -1
    if dir == 'w':
        x = 1
        y = 0
    elif dir == 's':
        x = -1
        y = 0
    elif dir == 'a':
        x = 0
        y = -1
    elif dir == 'd':
        x = 0
        y = 1
    else:
        print('Error: Invalid direction passed to simple_move: %s'%dir)
        return -1

    send_ned_target_rel(vehicle, x*dist, y*dist)
    return 1
    
def get_command(conn):
    return struct.unpack('<c',conn.read(struct.calcsize('<c')))[0]

def get_data(conn, dtype):
    if type(dtype) == str:
        d_len = struct.unpack('<L',conn.read(struct.calcsize('<L')))[0]
        d_len /= struct.calcsize('<'+dtype)

        encod = '<'+str(d_len)+dtype
        data = struct.unpack(encod,conn.read(struct.calcsize(encod)))
        return data
    else:
        print('invalid dtype: %s, must be string'%dtype)
        return None

def simple_yaw_rel(vehicle, angle):
    if angle > 0:
        d = 1
    else:
        d = -1
    condition_yaw(vehicle, angle, direction=d, rate=20, relative=True)
    return 1
