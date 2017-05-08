import socket
import io
import picamera
import sys
import struct


server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.sensor_mode = 7
camera.shutter_speed = 10000

stream = io.BytesIO()
while True:
    connection = server_socket.accept()[0].makefile('rwb')
    print(connection)
    try:
        while True:
            command = connection.read(1)
            if command != b'':
                print(command)
                if command == b'p':
                    camera.capture(stream, 'jpeg')
                    connection.write(struct.pack('<L', stream.tell()))
                    connection.flush()
                    # Rewind the stream and send the image data over the wire
                    stream.seek(0)
                    connection.write(stream.read())
                    connection.flush()
                    # Reset the stream for the next capture
                    stream.seek(0)
                    stream.truncate()
    except:
        print('Error: %s'%sys.exc_info()[0], flush=True)
