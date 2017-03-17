import tensorflow as tf
import network as net
import utils as u
import params as p
from PIL import Image
from scipy import misc
import numpy as np
import time


class NeuralNet:

    def __init__(self, input_size, net_name='squeeze_normal-dev'):

        k = p.ANCHOR_COUNT
        gs = p.GRID_SIZE

        x_input = input_size[1]
        y_input = input_size[0]
        input_tensor = tf.placeholder(tf.float32, shape=[None,x_input,y_input,3], name='input_images')
        image = tf.image.resize_images(input_tensor, [256,256])

        #t_activations = net.create_small_net(image)
        t_activations = net.create_forward_net(image)

        k = p.ANCHOR_COUNT
        t_deltas = tf.slice(t_activations, [0,0,0,0], [-1,-1,-1,4*k])
        t_gammas = tf.sigmoid(tf.slice(t_activations, [0,0,0,4*k], [-1,-1,-1,k]))
        t_classes = tf.slice(t_activations, [0,0,0,5*k], [-1,-1,-1,p.OUT_CLASSES*k])
        t_chosen_anchor = tf.argmax(t_gammas, axis=3)
        self.all_out = [t_activations, t_deltas, t_gammas, t_classes, t_chosen_anchor]
        self.sess = tf.Session()

        print('loading network.. ', end='')

        saver = tf.train.Saver()
        saver.restore(self.sess, './networks/%s.cpt'%net_name)
        print('Done.')



    def run_images(self, images, cutoff=0.05):
        '''
        runs the neural net on a batch of input images.

        Inputs:
            images: batch of pictures as a [b, X, Y, C] numpy array.
                values between 0 and 255 (uint8 range)
            cutoff: value to clip boxes at.
                TODO: Change this. there should be NMS here

        Returns:
            Array of BoundingBox objects representing the found boxes.
        '''
        k = p.ANCHOR_COUNT
        gs = p.GRID_SIZE

        batch_size = 1#images.shape[0]
        #assert len(images.size) == 4,\
        #    'Error in run_images: Images should be supplied as a batch of [batch, x, y, c]!'
        input_tensor = tf.placeholder(tf.float32)
        start_time = time.time()
        activations, deltas, gammas, classes, chosen_anchor = \
                        self.sess.run(self.all_out, feed_dict={'input_images:0': images})
        print('Took %f seconds!'%(time.time()-start_time))

        gammas = np.reshape(gammas, [-1, gs**2*k])
        chosen_anchor = np.reshape(chosen_anchor,[-1,gs**2])
        deltas = np.reshape(deltas, [-1, gs**2*k,4])
        anchors = u.create_anchors(gs)
        classes = np.reshape(classes, [-1,gs**2*k, p.OUT_CLASSES])
        class_numbers = np.argmax(classes, axis=2)

        box_list = []
        anchors = u.create_anchors(gs)
        for ib in range(batch_size):
            max_gamma= 0
            print('image %s'%ib)
            for idx in range(gs**2):
                ca = chosen_anchor[ib, idx]
                if(gammas[ib,idx*k+ca] > cutoff):
                    box = u.delta_to_box(deltas[ib,ca+idx*k,:],
                                anchors[ca+idx*k])
                    box_list.append(BoundingBox(u.trans_boxes(box),
                                                gammas[ib,idx*k+ca],
                                                class_numbers[ib,idx*k+ca]))
        return box_list


class BoundingBox:
    '''
    Struct to send info to the PIL front end.

    coords: 1x4 array of box coordinates. [x1, y1, x2, y2]
    confidence: confidence score for the box
    classification: numerical class given to box
    '''
    coords = [-1, -1, -1, -1]
    confidence = 0
    classification = -1

    def __init__(self, in_coords, in_gamma, in_class):
        self.coords = in_coords
        self.confidence = in_gamma
        self.classification = in_class
