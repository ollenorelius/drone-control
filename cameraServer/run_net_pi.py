from forward_net import NeuralNet
import picamera
import params as p
from PIL import Image
import time
import io
import numpy as np

picSize = (640,480)

nn = NeuralNet(picSize, 'squeeze_normal-drone')


camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.sensor_mode = 7
camera.shutter_speed = 10000
# Start a preview and let the camera warm up for 2 seconds
#camera.start_preview()
time.sleep(1)

stream = io.BytesIO()
start = time.time()
for foo in camera.capture_continuous(stream, 'jpeg', True):
    stream.seek(0)
    image = Image.open(stream)
    image.load()
    image.verify()
    bboxes = nn.run_images(
        [np.array(image.resize((p.IMAGE_SIZE,p.IMAGE_SIZE)))],
        cutoff=0.5)
    t = time.time()-start
    print('Took %s sec (%s fps)'%(t, 1/t))
    start = time.time()
