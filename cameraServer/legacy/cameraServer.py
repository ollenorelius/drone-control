import io
import socket
import struct
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os, sys
import tkinter
import numpy as np
import params as p

from forward_net import NeuralNet, BoundingBox


picSize = (1280,960) #(640,480)

def draw_boxes(boxes):
    mask = Image.new('RGBA', picSize, (255,255,255,0))
    d = ImageDraw.Draw(mask)
    fnt = ImageFont.truetype('/usr/share/fonts/truetype/ubuntu-font-family/UbuntuMono-R.ttf', 24)
    txt_offset_x = 0
    txt_offset_y = 25
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




# Start a socket listening for connections on 0.0.0.0:8000 (0.0.0.0 means
# all interfaces)
nn = NeuralNet(picSize, 'big_cups_slow_do05')
#nn = NeuralNet(picSize, 'squeeze_normal-drone_big_DO02_run2')
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 8000))
server_socket.listen(0)

def button_click_exit_mainloop (event):
    event.widget.quit() # this will cause mainloop to unblock.

root = tkinter.Tk()
root.bind("<Button>", button_click_exit_mainloop)
root.geometry('+%d+%d' % (100,100))
root.mainloop()

tkpi = ImageTk.PhotoImage(Image.new('RGB', picSize))
label_image = tkinter.Label(root, image=tkpi)
label_image.place(x=0,y=0,width=picSize[0],height=picSize[1])


# Accept a single connection and make a file-like object out of it
connection = server_socket.accept()[0].makefile('rwb')


while True:
    try:
        root.geometry('%dx%d' % picSize)
        while True:
            connection.write(b'a')
            connection.flush()
            # Read the length of the image as a 32-bit unsigned int. If the
            # length is zero, quit the loop
            image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                break
            # Construct a stream to hold the image data and read the image
            # data from the connection
            image_stream = io.BytesIO()
            image_stream.write(connection.read(image_len))
            # Rewind the stream, open it as an image with PIL and do some
            # processing on it
            image_stream.seek(0)
            image = Image.open(image_stream)
            image.load()
            image.verify()
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

            bboxes = nn.run_images(
                [np.array(image.resize((p.IMAGE_SIZE,p.IMAGE_SIZE)))],
                cutoff=0.4)

            ret_data_count = len(bboxes)
            connection.write(struct.pack('<L', ret_data_count))
            for box in bboxes:
                x = (box.coords[2] + box.coords[0])/2
                y = (box.coords[3] + box.coords[1])/2
                connection.write(struct.pack('<ff', x,y))
            connection.flush()
            image = image.convert('RGBA')
            image = image.resize(picSize,Image.ANTIALIAS)
            mask = draw_boxes(bboxes)

            image = Image.alpha_composite(image, mask)

            tkpi = ImageTk.PhotoImage(image)
            label_image.configure(image=tkpi)

            root.update()

            print('Image is %dx%d' % image.size)

    finally:
        connection.close()
        server_socket.close()

        server_socket.listen(0)
        connection = server_socket.accept()[0].makefile('rwb')
