import dronekit as dk
import math

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
        phi_y = (c[1]-0.5)*cam_y_fov

        theta_y = pitch + cam_mount_angle + phi_y
        theta_x = roll + phi_x

        y = math.tan(theta_x) * h
        r = math.sqrt(y**2+h**2)
        x = r * math.tan(theta_x)
        positions.append((x,y))
    return positions
