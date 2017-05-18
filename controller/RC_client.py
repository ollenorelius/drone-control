import socket
import io
import dronekit as dk
import RC_utils
import time
import sys


def client_handler(inbound_socket, addr, vehicle):
    #global vehicle
    print(inbound_socket)
    client_connection = inbound_socket.makefile('rwb')
    while True:
        t = time.time()
        command = RC_utils.get_command(client_connection)

        if command != b'':
            print(command)
            sys.stdout.flush()
            if command in [b'w',b's',b'a',b'd']:
                print 'got %s'%command
                RC_utils.simple_rel_move(vehicle, command)

            elif command == b'b':
                vehicle.armed = True

            elif command == b'n':
                vehicle.armed = False

            elif command == b'm':
                mode = RC_utils.get_data(client_connection, 's')[0]
                vehicle.mode = dk.VehicleMode(mode)

            elif command == b'p':
                pos = RC_utils.get_data(client_connection, 'f')
                send_ned_target(vehicle, n=pos[0], e=pos[1])

            elif command == b't':
                height = RC_utils.get_data(client_connection,'f')[0]
                print('Takeoff to %s m'%height)
                sys.stdout.flush()
                vehicle.simple_takeoff(height)

            elif command == b'y':
                ang = RC_utils.get_data(client_connection,'f')[0]
                RC_utils.simple_yaw_rel(vehicle, ang)

            elif command == b'r':
                RC_utils.simple_yaw_rel(vehicle, 10)

            elif command == b'l':
                RC_utils.simple_yaw_rel(vehicle, -10)



        '''except:
            print('Error: %s'%sys.exc_info()[0])
            print('Error: %s'%sys.exc_info()[1])
            print('Error: %s'%sys.exc_info()[2])
            client_connection.close()
            inbound_socket.close()'''
    return 0
