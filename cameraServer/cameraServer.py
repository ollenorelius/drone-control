#!/usr/bin/python3

import socket
import io
import picamera
import sys
import struct
import time
import threading
from queue import Queue


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
image_lock = threading.Lock()

image = b'asdf'


def time_op(start, name):
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %s' % (name, tt))
    return time.time()


def camera_thread():
    global image
    cam_stream = io.BytesIO()
    for foo in camera.capture_continuous(output=cam_stream,
                                         format='jpeg',
                                         use_video_port=True,
                                         quality=15,
                                         thumbnail=None):
        cam_stream.seek(0)
        image = cam_stream.read()
        cam_stream.seek(0)
        cam_stream.truncate()

        # if no clients are connected, just chill ad wait to save power.
        while(threading.active_count() < 3):
            time.sleep(0.2)


def network_thread(inbound_socket):
    client_connection = inbound_socket.makefile('rwb')
    # buf = bytearray([0])
    global image
    try:
        while True:
            t = time.time()
            command = client_connection.read(1)
            if command != b'':
                t = time_op(t, 'recv command')
                if command == b'p':
                    t = time.time()
                    with image_lock:
                        t = time_op(t, 'capture')
                        client_connection.write(struct.pack('<L', len(image)))
                        t = time_op(t, 'send header')
                        # Rewind the stream and send the image data over the wire
                        client_connection.write(image)
                    client_connection.flush()
                    t = time_op(t, 'send data')
            else:
                raise Exception('Stream broken!')
    except:
        print('Error: %s'%sys.exc_info()[0], flush=True)
        print('Error: %s'%sys.exc_info()[1], flush=True)
        print('Error: %s'%sys.exc_info()[2], flush=True)


threading.Thread(target=camera_thread, daemon=True).start()
while True:
    connection, addr = inbound_socket.accept()
    threading.Thread(target=network_thread, args=[connection]).start()
    print(connection)
