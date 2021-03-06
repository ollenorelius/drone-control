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
import threading
import utils as u

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
            print('Invalid argument: ', end='')
            print(arg[0])

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

yaw_pid_active = False
yaw_pid_active_tk = tkinter.BooleanVar()
check_yaw_pid = tkinter.Checkbutton(root,
                                    text='Yaw PID active',
                                    variable=yaw_pid_active_tk)
check_yaw_pid.pack()

pos_pid_active = False
pos_pid_active_tk = tkinter.BooleanVar()
check_pos_pid = tkinter.Checkbutton(root,
                                    text='Pos PID active',
                                    variable=pos_pid_active_tk)
check_pos_pid.pack()

root.update()
server_socket = socket.socket()
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.connect(('biffen.local', 8001))
connection = server_socket.makefile('rwb')

bboxes = []
bbox_time = time.time()

'''tracker_window = tkinter.Tk()
points = []

def tracker_thread():
    global points
    last_point = None
    while(True):
        send_command(cmd=b'o')
        pos = utils.get_data(RC_connection, 'f')

        if pos != last_point:
            points.append(pos)
            last_point = pos'''
class PID():
    var = 0
    accumulated_error = 0
    last_error = 0
    kp = 100
    kd = 0
    ki = 0
    i_max = 100
    setpoint = 0
    last_loop = 0
    first_run = True

    def __init__(self, kp, kd, ki, setpoint=0):
        self.kp = kp
        self.kd = kd
        self.ki = ki
        self.setpoint = setpoint

    def update(self, value):
        self.var = value
        error = self.var - self.setpoint
        dt = time.time() - self.last_loop
        D = (error - self.last_error)/dt
        I = error * dt + self.accumulated_error
        if I > self.i_max:
            I = self.i_max
        elif I < -self.i_max:
            I = -self.i_max
        pid_out = error * self.kp + self.kd * D + self.ki * I
        self.last_error = error
        self.last_loop = time.time()

        if not self.first_run:
            return pid_out
        else:
            self.first_run = False
            return 0

def yaw_pid_thread():
    angle_to_car = 0
    yaw_pid = PID(kp=200, kd=0, ki=0)
    dt = 0.1
    global yaw_pid_active
    while True:
        time.sleep(dt) #only run PID loop every dt seconds
        if yaw_pid_active:
            #if bboxes are older than dt, we processed them last frame.
            if time.time()-bbox_time < dt:
                if len(bboxes) > 0:
                    best_box = bboxes[0]
                    for box in bboxes:
                        if box.confidence > best_box.confidence:
                            best_box = box
                    box_center_x = (best_box.coords[0] + best_box.coords[2]) / 2
                    box_center_x = box_center_x - 0.5
                    cam_x_fov = 62.2*np.pi/180
                    angle_to_car = box_center_x * cam_x_fov

                    pid_out = yaw_pid.update(angle_to_car)

                    print('Angle PID: %s'%pid_out)
                    send_command(cmd='x', arg=(float(pid_out), float(dt)))

def pos_pid_thread():
    pos_pid = PID(kp=30, kd=0, ki=0)
    dt = 0.1
    global pos_pid_active
    while True:
        time.sleep(dt) #only run PID loop every dt seconds
        if pos_pid_active:
            #if bboxes are older than dt, we processed them last frame.
            if time.time()-bbox_time < dt:
                if len(bboxes) > 0:
                    best_box = bboxes[0]
                    for box in bboxes:
                        if box.confidence > best_box.confidence:
                            best_box = box

                    pos = u.get_relative_target_coords_fixed_drone([best_box.coords])
                    dist_to_car = pos[0][1]
                    pid_out = pos_pid.update(dist_to_car)
                    print('car pos is: ', end='')
                    print(pos)
                    print('Pos PID: %s'%pid_out)
                    send_command(cmd='v', arg=(float(-pid_out), float(dt)))


threading.Thread(target=yaw_pid_thread, daemon=True).start()
threading.Thread(target=pos_pid_thread, daemon=True).start()

pickle_stream = io.BytesIO()
image_stream = io.BytesIO()

while True:
    yaw_pid_active = yaw_pid_active_tk.get()
    pos_pid_active = pos_pid_active_tk.get()
    # Read the length of the image as a 32-bit unsigned int. If the
    # length is zero, quit the loop
    t = time.time()
    connection.write(struct.pack('<c', b'c'))
    connection.flush()
    pickle_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
    pickle_stream.seek(0)
    pickle_stream.write(connection.read(pickle_len))
    pickle_stream.seek(0)
    bboxes = pickle.loads(pickle_stream.read())
    bbox_time = time.time()

    connection.write(struct.pack('<c', b'p'))
    connection.flush()

    image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
    if not image_len:
        break
    # Construct a stream to hold the image data and read the image
    # data from the connection
    image_stream.seek(0)
    image_stream.write(connection.read(image_len))
    # Rewind the stream, open it as an image with PIL and do some
    # processing on it
    image_stream.seek(0)
    image = Image.open(image_stream)
    #image.load()
    #image.verify()
    #image = image.transpose(Image.FLIP_TOP_BOTTOM)

    image = image.convert('RGBA')
    mask = draw_boxes(bboxes)
    image = Image.alpha_composite(image, mask)
    image = image.convert('RGB')

    #root.geometry('%dx%d' % picSize)
    tkpi = ImageTk.PhotoImage(image.resize(picSize,Image.ANTIALIAS))
    label_image.configure(image=tkpi)

    root.update()
    print('%.3f FPS\r'%(1/(time.time()-t)), end='')
