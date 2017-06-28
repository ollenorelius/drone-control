"""Thread for handling a single client connection."""
import dronekit as dk
import RC_utils
import sys
import threading
import time
import RPi.GPIO as GPIO


def beep(duration, freq):
    """Emit a short beep."""
    def thread_func(duration, freq):
        global Buzz
        Buzz.ChangeFrequency(freq)  # 440 is initial frequency.
        Buzz.start(50)
        time.sleep(duration)
        Buzz.stop()
        return 0
    threading.Thread(target=thread_func, args=(duration, freq)).start()


def client_handler(inbound_socket, addr, vehicle):
    """
    Handle a single client connection.

    Basically a big loop that polls the connection supplied for single bytes
    and responds to them.

    Inputs:
        inbound_socket: socket returned by the servers accept() method.
        addr: IP to client. Currently unused.
        vehicle: dronekit vehicle refering to the drone.

    Returns:
        None. This method is just a loop, which excepts out when disconnected.
    """
    print(inbound_socket)
    client_connection = inbound_socket.makefile('rwb')
    RC_utils.set_home(vehicle, 57.704996, 11.963963, 0)
    while True:
        command = RC_utils.get_command(client_connection)

        if command != b'':
            print(command)
            sys.stdout.flush()
            if command == b'w':
                RC_utils.override_interval(vehicle, 'pitch', 1450, 0.1)
            if command == b's':
                RC_utils.override_interval(vehicle, 'pitch', 1550, 0.1)
            if command == b'a':
                RC_utils.override_interval(vehicle, 'roll', 1450, 0.1)
            if command == b'd':
                RC_utils.override_interval(vehicle, 'roll', 1550, 0.1)

            elif command == b'b':
                vehicle.armed = True

            elif command == b'n':
                vehicle.armed = False

            elif command == b'm':
                mode = RC_utils.get_data(client_connection, 's')[0]
                vehicle.mode = dk.VehicleMode(mode)

            elif command == b'p':
                pos = RC_utils.get_data(client_connection, 'f')
                RC_utils.send_ned_target(vehicle, n=pos[0], e=pos[1])

            elif command == b't':
                height = RC_utils.get_data(client_connection, 'f')[0]
                print('Takeoff to %s m' % height)
                sys.stdout.flush()
                vehicle.simple_takeoff(height)

            elif command == b'y':
                ang = RC_utils.get_data(client_connection, 'f')[0]
                RC_utils.simple_yaw_rel(vehicle, ang)

            elif command == b'x':
                val, dur = RC_utils.get_data(client_connection, 'f')
                print('Got yaw val %s and yaw time %s' % (val, dur))
                RC_utils.override_interval(vehicle, 'yaw', 1500+val, dur)

            elif command == b'v':
                val, dur = RC_utils.get_data(client_connection, 'f')
                print('Got pitch val %s and pitch time %s' % (val, dur))
                RC_utils.override_interval(vehicle, 'pitch', 1500+val, dur)

            elif command == b'r':
                RC_utils.simple_yaw_rel(vehicle, 10)

            elif command == b'l':
                RC_utils.simple_yaw_rel(vehicle, -10)

            elif command == b'o':
                pos = (vehicle.location.local_frame.north,
                       vehicle.location.local_frame.east,
                       vehicle.location.local_frame.down)
                RC_utils.send_data(client_connection, pos)

            elif command == b'c':
                att = (vehicle.attitude.roll,
                       vehicle.attitude.pitch,
                       vehicle.attitude.yaw)
                RC_utils.send_data(client_connection, att)

            elif command == b'q':
                freq, dur = RC_utils.get_data(client_connection, 'f')
                beep(dur, freq)

        '''except:
            print('Error: %s'%sys.exc_info()[0])
            print('Error: %s'%sys.exc_info()[1])
            print('Error: %s'%sys.exc_info()[2])
            client_connection.close()
            inbound_socket.close()'''
    return 0
