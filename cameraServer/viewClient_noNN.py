import io
import socket
import struct
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os, sys
import tkinter
import numpy as np
import params as p
import time
import pickle

picSize = (640,480)

RC_socket = socket.socket()
RC_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
RC_socket.connect(('dronepi.local', 8002))
RC_connection = RC_socket.makefile('rwb')

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
        #print('drawing box at ', end='')
        #print([x for x in box.coords])
        textpos = (p_coords[0] - txt_offset_x, p_coords[1] - txt_offset_y)
        d.text(textpos, 'Class %s at %s confidence'%(box.classification,box.confidence), font=fnt, fill='red')

    return mask
def send_command(cmd, arg=None):
    RC_connection.write(struct.pack('<c', bytes(cmd, encoding='ascii')))
    if arg != None:
        if type(arg) == str:
            RC_connection.write(struct.pack('<L', len(arg)))
            RC_connection.write(
                        struct.pack('<%ds'%len(arg),
                            bytes(arg, encoding='ascii')))
        elif type(arg) == float:
            RC_connection.write(struct.pack('<L', struct.calcsize('<f')))
            RC_connection.write(struct.pack('<f', arg))
        elif type(arg[0]) == float and type(arg[1]) == float:
            RC_connection.write(struct.pack('<L', struct.calcsize('<ff')))
            RC_connection.write(struct.pack('<ff', arg[0], arg[1]))
        else:
            print('Invalid argument: %s'%arg)

    RC_connection.flush()


def button_click_exit_mainloop (event):
    event.widget.quit() # this will cause mainloop to unblock.

def button_click_takeoff():
    send_command(cmd='t', arg=1.0)

def button_click_guided():
    send_command(cmd='m', arg='GUIDED')

def button_click_poshold():
    send_command(cmd='m', arg='POSHOLD')

def button_click_land():
    send_command(cmd='m', arg='LAND')

def button_click_arm():
    send_command(cmd='b')

def button_click_disarm():
    send_command(cmd='n')

def key_callback(event):
    if event.char in ['w','s','a','d']:
        send_command(event.char)
    if event.char == 'q':
        send_command(cmd='l')
    if event.char == 'e':
        send_command(cmd='r')
    print(event.char)
    sys.stdout.flush()

root = tkinter.Tk()
root.bind("<Button>", button_click_exit_mainloop)
root.bind("<Key>", key_callback)
#root.geometry('%dx%d+%d+%d' % (640,490,100,100))
root.mainloop()

tkpi = ImageTk.PhotoImage(Image.new('RGB', picSize))
label_image = tkinter.Label(root, image=tkpi)
label_image.pack()
#label_image.place(x=0,y=0,width=picSize[0],height=picSize[1])

button_takeoff = tkinter.Button(root,
                                    text='Take off',
                                    command= button_click_takeoff)
button_takeoff.pack()

button_arm = tkinter.Button(root,
                                    text='Arm',
                                    command= button_click_arm)
button_arm.pack()

button_disarm = tkinter.Button(root,
                                    text='Disarm',
                                    command= button_click_disarm)
button_disarm.pack()

button_guided = tkinter.Button(root,
                                    text='Guided Mode',
                                    command= button_click_guided)
button_guided.pack()

button_poshold = tkinter.Button(root,
                                    text='Poshold Mode',
                                    command= button_click_poshold)
button_poshold.pack()

button_land = tkinter.Button(root,
                                    text='Land',
                                    command= button_click_land)
button_land.pack()

root.update()
while(1):
    root.update()
