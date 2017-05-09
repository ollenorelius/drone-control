import socket
import io
import picamera
import sys
import struct
import time



inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8000))
inbound_socket.listen(0)

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.sensor_mode = 7
camera.shutter_speed = 10000
camera.framerate = 40
camera.rotation = 180

timing = False
def time_op(start, name):
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s'%(name, tt))
    return time.time()

stream = io.BytesIO()
while True:

    connection = inbound_socket.accept()[0].makefile('rwb')
    print(connection)
    try:
        while True:
            t = time.time()
            command = connection.read(1)
            t = time_op(t, 'recv command')
            if command != b'':
                #print(command)
                if command == b'p':
                    t = time.time()
                    camera.capture(stream, 'jpeg', use_video_port=True)
                    t = time_op(t, 'capture')
                    connection.write(struct.pack('<L', stream.tell()))
                    connection.flush()
                    t = time_op(t, 'send header')
                    # Rewind the stream and send the image data over the wire
                    stream.seek(0)
                    connection.write(stream.read())
                    connection.flush()
                    t = time_op(t, 'send data')
                    # Reset the stream for the next capture
                    stream.seek(0)
                    stream.truncate()
            else:
                raise Exception('Stream broken!')
    except:
        print('Error: %s'%sys.exc_info()[0], flush=True)
