import tensorflow as tf
import params as p

"""
Functions related to building the graphs.
"""


def create_small_net(input_tensor):
    with tf.name_scope("Convolutional_layers"):
        x_image = tf.reshape(input_tensor, [-1, p.IMAGE_SIZE,
                                                p.IMAGE_SIZE,
                                                p.IMAGE_CHANNELS])
        tf.summary.histogram('image',x_image)
        sq1 = conv_layer(x_image,7,96,'conv1')
        mp1 = max_pool_2x2(sq1,'max_pool1') #down to 128x128

        sq2 = create_fire_module(mp1, 16,64,64,'fire2')
        sq3 = create_fire_module(sq2, 32,128,128,'fire3')

        mp2 = max_pool_2x2(sq3,'max_pool2') # 64x64

        sq4 = create_fire_module(mp2, 32,128,128,'fire4')
        mp3 = max_pool_2x2(sq4,'max_pool3') #down to 32x32

        sq5 = create_fire_module(mp3, 64,256,256,'fire5')

        mp4 = max_pool_2x2(sq5,'max_pool4')#down to 16x16

        sq6 = create_fire_module(mp4, 64,256,256,'fire6')
        mp5 = max_pool_2x2(sq6,'max_pool5') # 8x8

        tf.summary.histogram('sq9', mp5)
        activations = get_activations(mp5)
        tf.summary.histogram('activations', activations)

        return activations

def create_forward_net(input_tensor):
    with tf.name_scope("Convolutional_layers"):
        x_image = tf.reshape(input_tensor, [-1, p.IMAGE_SIZE,
                                                p.IMAGE_SIZE,
                                                p.IMAGE_CHANNELS])
        sq1 = create_fire_module(x_image,32,64,64,'fire1')
        mp1 = max_pool_2x2(sq1,'max_pool1') #down to 128x128

        sq2 = create_fire_module(mp1, 16,64,64,'fire2')
        sq3 = create_fire_module(sq2, 16,64,64,'fire3')
        sq4 = create_fire_module(sq3, 32,128,128,'fire4')

        mp2 = max_pool_2x2(sq4,'max_pool2') # 64x64
        mp3 = max_pool_2x2(mp2,'max_pool3') #down to 32x32

        sq5 = create_fire_module(mp3, 32,128,128,'fire5')
        sq6 = create_fire_module(sq5, 48,192,192,'fire6')
        sq7 = create_fire_module(sq6, 48,192,192,'fire7')
        sq8 = create_fire_module(sq7, 64,256,256,'fire8')

        mp4 = max_pool_2x2(sq8,'max_pool4')#down to 16x16
        mp5 = max_pool_2x2(mp4,'max_pool5') # 8x8


        sq9 = create_fire_module(mp5, 64,256,256,'fire9')#(mp8, 64,256,256,512)
        tf.summary.histogram('sq9', sq9)
        activations = get_activations(sq9)
        tf.summary.histogram('activations', activations)

        return activations


def create_fire_module(input_tensor,s1,e1,e3,name):
    """
        Adds a Fire module to the graph.

        In:
            input_tensor: the preceding tf.Tensor.
            s1: number of 1x1 squeeze kernels.
            e1: number of 1x1 expand kernels.
            e3: number of 3x3 expand kernels.
            name: Name of the layer

        Out:
            tens: Activation volume (tf.Tensor)
    """
    with tf.name_scope(name):
        sq = squeeze(input_tensor,s1)
        tens = expand(sq,e1,e3)
        return tens


def squeeze(input_tensor, s1):
    """
        Creates a squeeze operation on input_tensor.
        In:
            input_tensor: the preceding tf.Tensor.
            s1: number of 1x1 kernels.

        Out:
            Activation volume. (tf.Tensor)
    """
    with tf.name_scope('squeeze'):
        inc = input_tensor.get_shape()[3]
        w = weight_variable([1,1,int(inc),s1], 'w_1x1')
        b = bias_variable([s1],'b_1x1')
        return layer_activation(conv2d(input_tensor, w) + b)


def expand(input_tensor, e1, e3):
    """
        Creates a expand operation on input_tensor.
        In:
            input_tensor: the preceding tf.Tensor.
            e1: number of 1x1 kernels.
            e3: number of 3x3 kernels.

        Out:
            Activation volume. (tf.Tensor)
    """
    with tf.name_scope('expand'):
        inc = int(input_tensor.get_shape()[3])
        w3 = weight_variable([3,3,inc,e3],'w_3x3')
        b3 = bias_variable([e3],'b_3x3')
        c3 = layer_activation(conv2d(input_tensor, w3) + b3)

        w1 = weight_variable([1,1,inc,e1],'w_1x1')
        b1 = bias_variable([e1],'b_1x1')
        c1 = layer_activation(conv2d(input_tensor, w1) + b1)

        return tf.concat([c1,c3],3)


def get_activations(input_tensor):
    """
        Gets activations by 3x3 convolution as described in the
        SqueezeDet paper.

        In:
            Activation volume from previous convolutional layers. (tf.Tensor)

        Out:
            tf.Tensor of class scores. (batch x classes)
    """
    with tf.name_scope('activation_layer'):
        inc = int(input_tensor.get_shape()[3])
        out_count = p.ANCHOR_COUNT*(p.OUT_CLASSES + p.OUT_COORDS + p.OUT_CONF)
        w = weight_variable([3, 3, inc, out_count],'w_activations')
        b = bias_variable([out_count],'b_activations')
        tens = conv2d(input_tensor, w) + b

        return tens

def conv_layer(input_tensor, size, depth, name):
    with tf.name_scope(name):
        inc = int(input_tensor.get_shape()[3])
        w = weight_variable([size,size,inc,depth],'w_conv')
        b = bias_variable([depth],'b_conv')
        c = layer_activation(conv2d(input_tensor, w) + b)
        return c

def layer_activation(input_tensor):
    '''
    Convenience function for trying different activations.
    '''
    return tf.nn.relu(input_tensor)

def weight_variable(shape,name):
    initial = tf.truncated_normal(shape, stddev=0.1)
    return tf.Variable(initial, name=name)


def bias_variable(shape,name):
    initial = tf.constant(0.1, shape=shape)
    return tf.Variable(initial, name=name)


def conv2d(x,W):
    return tf.nn.conv2d(x,W,strides=[1,1,1,1], padding='SAME')

def max_pool_2x2(x, name):
    with tf.name_scope('MP_' + name):
        return tf.nn.max_pool(x,
                          ksize=[1,2,2,1],
                          strides=[1,2,2,1],
                          padding='SAME',
                          name=name)
