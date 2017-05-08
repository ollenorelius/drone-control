import io
import socket
import struct
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os, sys
import numpy as np
import params as p
import time
import pickle

from forward_net import NeuralNet, BoundingBox
from queue import Queue
import threading

picSize = (640,480)
# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)

client_socket = socket.socket()
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client_socket.bind(('0.0.0.0', 8001))
client_socket.listen(0)

job_queue = Queue()
result_queue = Queue()
last_pic = Image.new('RGBA', picSize, (255,255,255,0))


def client_handler(client_socket, addr, job_queue, result_queue, last_pic):

    print(client_socket)
    def draw_boxes(boxes):
        mask = Image.new('RGBA', picSize, (255,255,255,0))
        d = ImageDraw.Draw(mask)
        fnt = ImageFont.truetype('/usr/share/fonts/truetype/ubuntu-font-family/UbuntuMono-R.ttf', 12)
        txt_offset_x = 0
        txt_offset_y = 20
        for box in boxes:
            p_coords = [box.coords[0]*picSize[0],
                        box.coords[1]*picSize[1],
                        box.coords[2]*picSize[0],
                        box.coords[3]*picSize[1]]
            d.rectangle(p_coords, outline='red')
            print('drawing box at ', end='')
            print([x for x in box.coords])
            textpos = (p_coords[0] - txt_offset_x, p_coords[1] - txt_offset_y)
            d.text(textpos, 'Class %s at %s confidence'%(box.classification,box.confidence), font=fnt, fill='red')

        return mask
    try:
        camera_socket = socket.socket()
        camera_socket.connect(('dronepi.local', 8000))
        camera_connection = camera_socket.makefile('rwb')

        client_connection = client_socket.makefile('rwb')
        image_stream = io.BytesIO()
        while True:
            command = struct.unpack('<c',client_connection.read(struct.calcsize('<c')))[0]
            if command != b'':
                print(command)
                if command == b'p':

                    last_pic.save(image_stream, format='jpeg')
                    client_connection.write(struct.pack('<L', image_stream.tell()))
                    # Rewind the stream and send the image data over the wire
                    image_stream.seek(0)
                    client_connection.write(image_stream.read())
                    client_connection.flush()
                    #reset stream
                    image_stream.seek(0)
                    image_stream.truncate()

                elif command == b'c':
                    camera_connection.write(b'p')
                    camera_connection.flush()
                    image_len = struct.unpack('<L', camera_connection.read(struct.calcsize('<L')))[0]
                    if not image_len:
                        break
                    # Construct a stream to hold the image data and read the image
                    # data from the connection
                    image_stream = io.BytesIO()
                    image_stream.write(camera_connection.read(image_len))
                    # Rewind the stream, open it as an image with PIL and do some
                    # processing on it
                    image_stream.seek(0)
                    image = Image.open(image_stream)
                    image.load()
                    image.verify()
                    image = image.transpose(Image.FLIP_TOP_BOTTOM)
                    #job_queue.put(image)
                    #job_queue.join()
                    bboxes = []#result_queue.get(False)
                    box_pickle = pickle.dumps(bboxes)

                    pickle_size = len(box_pickle)
                    client_connection.write(struct.pack('<L', pickle_size))
                    client_connection.write(box_pickle)
                    client_connection.flush()

                    last_pic = image
    except:
        print('Error: %s'%sys.exc_info()[0], flush=True)
        client_connection.close()
        camera_connection.close()
        client_socket.close()
        camera_socket.close()
    return 0

def NNRunner(input_queue, output_queue):
    nn = NeuralNet(picSize, 'normal_fast_DO05_class_fix3_anch')
    sys.stdout.flush()
    while True:
        pic = input_queue.get(True)
        boxes = nn.run_images([np.asarray(pic.resize((p.IMAGE_SIZE,p.IMAGE_SIZE)))])
        output_queue.put(boxes)
        input_queue.task_done()

print('Neural net server running!', flush=True)
threading.Thread(target=NNRunner, args=(job_queue, result_queue), daemon=True).start()

while True:
    c, addr = client_socket.accept()
    args = (c, addr, job_queue, result_queue, last_pic)
    threading.Thread(target=client_handler,args=args).start()
    print('Client connected: %s:%s'%addr)
