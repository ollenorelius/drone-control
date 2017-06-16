"""Container for the Neural Net class."""
import tensorflow as tf
import utils as u
import params as p
import numpy as np
import time
from tensorflow.python.platform import gfile
import sys
from PIL import Image
from bbox import BoundingBox


class NeuralNet:
    """Container class for Tensorflow NN models."""

    def __init__(self, net_name='squeeze_normal-drone'):
        """
        Constructor method.

        Input:
            net_name: name of the folder containing the saved weights for the
            network. This should not include 'networks/', this is implied.
        """
        k = p.ANCHOR_COUNT
        print('loading network.. ', end='', flush=True)
        folder_name = './networks/%s' % net_name
        with gfile.FastGFile(folder_name + "/latest.pb", 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='')

        self.graph = tf.get_default_graph()
        self.inp_batch = self.graph.get_tensor_by_name('Input_batching/batch:0')
        t_activations = self.graph.get_tensor_by_name('activation/activations:0')
        #self.do = self.graph.get_tensor_by_name('Placeholder:0')
        # print([n.name for n in tf.get_default_graph().as_graph_def().node])
        print('Done!')
        sys.stdout.flush()
        k = p.ANCHOR_COUNT
        t_deltas = tf.slice(t_activations, [0, 0, 0, 0], [-1, -1, -1, 4*k])
        t_gammas = tf.sigmoid(tf.slice(t_activations,
                                       [0, 0, 0, 4*k],
                                       [-1, -1, -1, k]))
        t_classes = tf.slice(t_activations,
                             [0, 0, 0, 5*k],
                             [-1, -1, -1, p.OUT_CLASSES * k])
        t_chosen_anchor = tf.argmax(t_gammas, axis=3)
        self.all_out = [t_activations,
                        t_deltas,
                        t_gammas,
                        t_classes,
                        t_chosen_anchor]

        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)

    def run_images(self, images, cutoff=0.05):
        """
        Run the neural net on a batch of input images.

        Inputs:
            images: batch of pictures as a [b, X, Y, C] numpy array.
                values between 0 and 255 (uint8 range)
            cutoff: value to clip boxes at.

        Returns:
            Array of BoundingBox objects representing the found boxes.
        """
        k = p.ANCHOR_COUNT
        gs = p.GRID_SIZE

        batch_size = 1
        start_time = time.time()
        activations, deltas, gammas, classes, chosen_anchor = \
            self.sess.run(self.all_out,
                          feed_dict={self.inp_batch: images})  # ,
                                     # self.do: 1.0})
        print('Took %f seconds!' % (time.time()-start_time))

        gammas = np.reshape(gammas, [-1, gs**2*k])
        chosen_anchor = np.reshape(chosen_anchor, [-1, gs**2])
        deltas = np.reshape(deltas, [-1, gs**2*k, 4])
        classes = np.reshape(classes, [-1, gs**2*k, p.OUT_CLASSES])
        class_numbers = np.argmax(classes, axis=2)

        box_list = []
        anchors = u.create_anchors(gs)

        for ib in range(batch_size):
            boxes = u.delta_to_box(deltas[ib], anchors)
            nms_indices = tf.image.non_max_suppression(u.trans_boxes(boxes),
                                                       gammas[ib],
                                                       5,
                                                       iou_threshold=0.0) \
                            .eval(session=self.sess)

            selected_boxes = boxes[nms_indices]
            selected_gamma = gammas[ib, nms_indices]
            selected_class = class_numbers[ib, nms_indices]
            selected_class_scores = classes[ib, nms_indices]

            for i, box in enumerate(selected_boxes):
                sm_scores = u.softmax(selected_class_scores[i])
                conf = selected_gamma[i] * sm_scores[selected_class[i]]
                if conf > cutoff:
                    print(conf)
                    box_list.append(BoundingBox(u.trans_boxes(box),
                                                conf,
                                                selected_class[i]))

        return box_list

    def export_weights(self):
        """Save first layer weights as images."""
        name = 'Convolutional_layers/conv1/w_conv:0'
        w_t = self.graph.get_tensor_by_name(name)
        with self.sess:
            w = w_t.eval()
            #print(w.shape)
            for i in range(w.shape[3]):
                pic = w[:, :, :, i]
                pic -= np.min(pic)
                pic /= np.max(pic)
                pic *= 255
                #print(pic)
                im = Image.fromarray(pic.astype('uint8'))
                im.save('filters/%s.jpg' % i)
