import io
import socket
import struct
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os, sys
import numpy as np
import params as p
import time
import pickle

from forward_net import NeuralNet
from utils import BoundingBox
from queue import Queue
import threading

picSize = (640,480)
# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)

inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8001))
inbound_socket.listen(0)

job_queue = Queue()
result_queue = Queue()
#last_pic = Queue()
last_pic = Image.new('RGBA', picSize, (255,255,255,0))

timing = False
def time_op(start, name):
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %.6f'%(name, tt))
    return time.time()

def client_handler(inbound_socket, addr, job_queue, result_queue):
    global last_pic
    print(inbound_socket)

    try:
        camera_socket = socket.socket()
        camera_socket.connect(('dronepi.local', 8000))
        camera_connection = camera_socket.makefile('rwb')

        client_connection = inbound_socket.makefile('rwb')
        image_stream = io.BytesIO()
        while True:
            t = time.time()
            command = struct.unpack('<c',client_connection.read(struct.calcsize('<c')))[0]
            t = time_op(t, 'recv command')
            if command != b'':
                #print(command)
                if command == b'p':
                    last_pic.save(image_stream, format='jpeg', quality=85, thumbnail=None)
                    t = time_op(t, 'save pic')
                    client_connection.write(struct.pack('<L', image_stream.tell()))
                    t = time_op(t, 'send header')
                    # Rewind the stream and send the image data over the wire
                    image_stream.seek(0)
                    client_connection.write(image_stream.read())
                    client_connection.flush()
                    t = time_op(t, 'send pic')
                    #reset stream
                    image_stream.seek(0)
                    image_stream.truncate()

                elif command == b'c':
                    camera_connection.write(b'p')
                    camera_connection.flush()
                    t = time_op(t, 'send cam request')
                    image_len = struct.unpack('<L', camera_connection.read(struct.calcsize('<L')))[0]
                    t = time_op(t, 'recv header')
                    if not image_len:
                        print('Received image length of 0, quitting!')
                        break
                    # Construct a stream to hold the image data and read the image
                    # data from the connection
                    image_stream.write(camera_connection.read(image_len))
                    t = time_op(t, 'recv pic')
                    # Rewind the stream, open it as an image with PIL and do some
                    # processing on it
                    image_stream.seek(0)
                    image = Image.open(image_stream)
                    #image.load()
                    #image.verify()

                    t = time_op(t, 'open pic & process')
                    job_queue.put(image)
                    job_queue.join()
                    t = time_op(t, 'NN')

                    image_stream.seek(0)
                    image_stream.truncate()

                    bboxes = result_queue.get(False)
                    box_pickle = pickle.dumps(bboxes, protocol=3)
                    pickle_size = len(box_pickle)
                    t = time_op(t, 'pickle')
                    client_connection.write(struct.pack('<L', pickle_size))
                    client_connection.write(box_pickle)
                    client_connection.flush()
                    t = time_op(t, 'send pickle')

                    last_pic = image

                elif command == b'd':
                    camera_connection.write(b'p')
                    camera_connection.flush()
                    t = time_op(t, 'send cam request')
                    image_len = struct.unpack('<L', camera_connection.read(struct.calcsize('<L')))[0]
                    t = time_op(t, 'recv header')
                    if not image_len:
                        print('Received image length of 0, quitting!')
                        break
                    # Construct a stream to hold the image data and read the image
                    # data from the connection
                    image_stream.write(camera_connection.read(image_len))
                    t = time_op(t, 'recv pic')
                    # Rewind the stream, open it as an image with PIL and do some
                    # processing on it
                    image_stream.seek(0)
                    image = Image.open(image_stream)
                    #image.load()
                    #image.verify()

                    t = time_op(t, 'open pic & process')
                    job_queue.put(image)
                    job_queue.join()
                    t = time_op(t, 'NN')

                    image_stream.seek(0)
                    image_stream.truncate()

                    bboxes = result_queue.get(False)

                    box_count = len(bboxes)
                    client_connection.write(struct.pack('<L', box_count))
                    for box in bboxes:
                        data = [box.coords[0],
                            box.coords[1],
                            box.coords[2],
                            box.coords[3],
                            box.confidence,
                            box.classification]
                        print(data)
                        client_connection.write(struct.pack('<ffffff',data[0],data[1],data[2],data[3],data[4],data[5]))
                    client_connection.flush()
                    t = time_op(t, 'send tuples')

                    last_pic = image
    except:
        print('Error: %s'%sys.exc_info()[0], flush=True)
        print('Error: %s'%sys.exc_info()[1], flush=True)
        print('Error: %s'%sys.exc_info()[2], flush=True)
        client_connection.close()
        camera_connection.close()
        inbound_socket.close()
        camera_socket.close()
    return 0

def ProcessRunner(input_queue, output_queue):
    nn = NeuralNet(picSize, 'normal_fast_DO05_class_fix3_anch')
    while True:
        pic = input_queue.get(True)
        boxes = nn.run_images([np.asarray(pic.resize((p.IMAGE_SIZE,p.IMAGE_SIZE)))], cutoff=0.35)
        output_queue.put(boxes)
        input_queue.task_done()

print('Neural net server running!', flush=True)
threading.Thread(target=NNRunner, args=(job_queue, result_queue), daemon=True).start()

while True:
    c, addr = inbound_socket.accept()
    args = (c, addr, job_queue, result_queue)
    threading.Thread(target=client_handler,args=args).start()
    print('Client connected: %s:%s'%addr)
