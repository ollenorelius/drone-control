"""
Main file for running the neural net server.

Waits for connections from any source at port 8001.
"""
import io
import socket
import struct
from PIL import Image, ImageDraw, ImageFont
import sys
import numpy as np
import params as p
import time
import pickle

from forward_net import NeuralNet

from queue import Queue
import threading

picSize = (640, 480)
# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)

inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8001))
inbound_socket.listen(0)

job_queue = Queue()
result_queue = Queue()

last_pic = Image.new('RGB', picSize, (155, 245, 210, 0))
timing = False

if len(sys.argv) > 1 and sys.argv[1] == '-test':
    for i in range(20):
        job_queue.put(last_pic.resize((512,512)))


def time_op(start, name):
    """Quick method for timing operations."""
    tt = time.time() - start
    if timing:
        print('Time taken for %s: %.6f' % (name, tt))
    return time.time()


def client_handler(inbound_socket, addr, job_queue, result_queue):
    """
    Main client handler thread.

    One of these start for each client connecting, and it should close
    tidily upon disconnect.

    Input:
        inbound_socket: socket for connecting client
        addr: ip address for connecting client
        job_queue: queue for received images. This is emptied by the NN thread
            and the result is placed in result_queue. (PIL Image)
        result_queue: Where the NN puts its calculated bounding boxes.
            (list of BoundingBox)
    Returns: nothing.
    """
    global last_pic
    print(inbound_socket)

    def draw_boxes(boxes):
        mask = Image.new('RGBA', picSize, (255, 255, 255, 0))
        d = ImageDraw.Draw(mask)
        fnt = ImageFont.truetype(p.FONT_PATH, 12)
        txt_offset_x = 0
        txt_offset_y = 20
        for box in boxes:
            p_coords = [box.coords[0]*picSize[0],
                        box.coords[1]*picSize[1],
                        box.coords[2]*picSize[0],
                        box.coords[3]*picSize[1]]
            d.rectangle(p_coords, outline='red')
            print('drawing box at ', end='')
            # print([x for x in box.coords])
            textpos = (p_coords[0] - txt_offset_x, p_coords[1] - txt_offset_y)
            d.text(textpos, 'Class %s at %s confidence' %
                   (box.classification, box.confidence), font=fnt, fill='red')

        return mask
    try:
        camera_socket = socket.socket()
        camera_socket.connect(('dronepi.local', 8000))
        camera_connection = camera_socket.makefile('rwb')

        client_connection = inbound_socket.makefile('rwb')
        image_stream = io.BytesIO()
        char_len = struct.calcsize('<c')
        long_len = struct.calcsize('<L')
        while True:
            t = time.time()
            command = struct.unpack('<c', client_connection.read(char_len))[0]
            t = time_op(t, 'recv command')
            if command != b'':
                if command == b'p':
                    last_pic.save(image_stream,
                                  format='jpeg',
                                  quality=85,
                                  thumbnail=None)
                    t = time_op(t, 'save pic')
                    header = struct.pack('<L', image_stream.tell())
                    client_connection.write(header)
                    t = time_op(t, 'send header')
                    # Rewind the stream and send the image data over the wire
                    image_stream.seek(0)
                    client_connection.write(image_stream.read())
                    client_connection.flush()
                    t = time_op(t, 'send pic')
                    # reset stream
                    image_stream.seek(0)
                    image_stream.truncate()

                elif command == b'c':
                    camera_connection.write(b'p')
                    camera_connection.flush()
                    t = time_op(t, 'send cam request')
                    image_len_raw = camera_connection.read(long_len)
                    image_len = struct.unpack('<L', image_len_raw)[0]
                    t = time_op(t, 'recv header')
                    if not image_len:
                        print('Received image length of 0, quitting!')
                        break
                    # Construct a stream to hold the image data and
                    # read the image data from the connection
                    image_stream.write(camera_connection.read(image_len))
                    t = time_op(t, 'recv pic')
                    # Rewind the stream, open it as an image with PIL and
                    # do some processing on it
                    image_stream.seek(0)
                    image = Image.open(image_stream)

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
                    image_len_raw = camera_connection.read(long_len)
                    image_len = struct.unpack('<L', image_len_raw)[0]
                    t = time_op(t, 'recv header')
                    if not image_len:
                        print('Received image length of 0, quitting!')
                        break
                    # Construct a stream to hold the image data and read
                    # the image data from the connection

                    image_stream.write(camera_connection.read(image_len))
                    t = time_op(t, 'recv pic')
                    # Rewind the stream, open it as an image with PIL and
                    # do some processing on it
                    image_stream.seek(0)
                    image = Image.open(image_stream)

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
                        #print(data)
                        client_connection.write(struct.pack('<ffffff',
                                                            data[0],
                                                            data[1],
                                                            data[2],
                                                            data[3],
                                                            data[4],
                                                            data[5]))
                    client_connection.flush()
                    t = time_op(t, 'send tuples')

                    last_pic = image
    except:
        print('Error: %s' % sys.exc_info()[0], flush=True)
        print('Error: %s' % sys.exc_info()[1], flush=True)
        print('Error: %s' % sys.exc_info()[2], flush=True)
        client_connection.close()
        camera_connection.close()
        inbound_socket.close()
        camera_socket.close()
        return 0


def NNRunner(input_queue, output_queue):
    """Thread for running the neural net."""
    nn = NeuralNet('tiny_res_slow')
    # nn.export_weights()
    while True:
        pic = input_queue.get(True).resize((p.IMAGE_SIZE, p.IMAGE_SIZE))
        boxes = nn.run_images([np.asarray(pic)], cutoff=0.2)
        output_queue.put(boxes)
        input_queue.task_done()


print('Neural net server running!', flush=True)
threading.Thread(target=NNRunner,
                 args=(job_queue, result_queue),
                 daemon=True).start()

while True:
    c, addr = inbound_socket.accept()
    args = (c, addr, job_queue, result_queue)
    threading.Thread(target=client_handler, args=args).start()
    print('Client connected: %s:%s' % addr)
