import tensorflow as tf
import params as p
import numpy as np

class BoundingBox(object):
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

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def create_anchors(grid_size):
    """
        Creates a list of all anchor coordinates.
        Input: Grid size to distribute anchors over.

        Returns: (K*X*Y) x 4 tensor containing coordinates in (x,y,w,h)-form
            in a, y, x order:
    """
    x = np.linspace(0,1,grid_size)
    xv, yv = np.meshgrid(x,x)
    anchors = []
    for ix in range(len(xv)):
        for iy in range(len(yv)):
            for i in range(p.ANCHOR_COUNT):
                anchors.append((xv[ix,iy], yv[ix,iy], p.ANCHOR_SIZES[i][0]/2, p.ANCHOR_SIZES[i][1]/2))

    assert (len(anchors), len(anchors[1])) == (p.ANCHOR_COUNT * p.GRID_SIZE**2, 4), \
     "ERROR: create_anchors made a matrix of shape %i,%i" % (len(anchors), len(anchors[1]))

    return np.array(anchors)

def intersection(bbox, anchors):
    """
    Computes intersection of a SINGLE bounding box and all anchors.

    bbox: coordinate tensor: 4x1 (x, y, w, h)
    anchors: coordinate tensor: 4x(X*Y*K) with XY being number of grid points

    returns: a 1x(X*Y*K) tensor containing all anchor intersections.

    """

    assert np.shape(bbox) == (4,), \
                    "Invalid shape of bbox in utils.intersection:%s"%np.shape(bbox)

    assert np.shape(anchors)[0] == 4, \
                    "Invalid shape of anchors in utils.intersection!"
    bbox_t = trans_boxes(np.transpose(bbox))
    anchors_t = trans_boxes(np.transpose(anchors))

    p1 = np.minimum(bbox_t[2], anchors_t[:,2])\
            - np.maximum(bbox_t[0], anchors_t[:,0])
    p2 = np.minimum(bbox_t[3], anchors_t[:,3])\
            - np.maximum(bbox_t[1], anchors_t[:,1])

    p1_r = np.maximum(p1,0) #If this is negative, there is no intersection
    p2_r = np.maximum(p2,0) # so it is rectified

    return np.multiply(p1_r,p2_r)

def union(bbox, anchors, intersections):
    """
    Computes union of a SINGLE bounding box and all anchors.

    bbox: coordinate array: 4x1 (x, y, w, h)
    anchors: coordinate array: 4x(X*Y*K) with XY being number of grid points
    intersections: array containing all intersections computed using
        intersection(). used to avoid double calculation.


    returns: a 1x(X*Y*K) array containing all anchor unions.

    """

    assert np.shape(bbox) == (4,), \
                    "Invalid shape of bbox in utils.union:%s"%np.shape(bbox)

    assert np.shape(anchors)[0] == 4, \
                    "Invalid shape of anchors in utils.union:%s"%np.shape(anchors)

    box_area = bbox[2]*bbox[3]
    anchor_areas = anchors[2,:]*anchors[3,:]

    return box_area + anchor_areas - intersections

def intersection_over_union(bbox, anchors):
    '''
        Computes IOU for all anchors with one bounding box.

        Inputs:
            bbox: coordinate array: 4x1 (x, y, w, h)
            anchors: coordinate array: 4x(X*Y*K) with XY being number of grid points

        Returns:
            IOU: array of IOUs. (XYK) x 1

    '''

    intersections = intersection(bbox, anchors)
    unions = union(bbox, anchors, intersections)

    return intersections/unions

def trans_boxes(coords):
    """
        Transforms coordinates from x, y, w, h to x1, y1, x2, y2.

        Input: a Nx4 matrix of coordinates for N boxes.

        Returns: a Nx4 matrix of transformed coordinates.
    """
    coords = np.transpose(coords)
    t_coords = []
    t_coords.append(coords[0] - coords[2]/2)
    t_coords.append(coords[1] - coords[3]/2)
    t_coords.append(coords[0] + coords[2]/2)
    t_coords.append(coords[1] + coords[3]/2)
    t_coords = np.transpose(t_coords)
    return t_coords

def inv_trans_boxes(coords):
    """
        Transforms coordinates from x1, y1, x2, y2 to x, y, w, h

        Input: a Nx4 matrix of coordinates for N boxes.

        Returns: a Nx4 matrix of transformed coordinates.
    """
    coords = np.transpose(coords)
    t_coords = []
    t_coords.append((coords[0] + coords[2])/2)
    t_coords.append((coords[1] + coords[3])/2)
    t_coords.append(coords[2] - coords[0])
    t_coords.append(coords[3] - coords[1])
    t_coords = np.transpose(t_coords)
    assert np.shape(t_coords)[1] == 4, \
            "invalid shape in inv_trans_boxes: %i,%i" % np.shape(t_coords)
    return t_coords

def get_stepped_slice(in_tensor, start, length):
    in_shape = in_tensor.get_shape().as_list()
    in_depth = in_shape[3]
    stride = (1+4+p.OUT_CLASSES) # gammas + deltas + classes,
                                 # the number of things for each anchor
                                 # so we can stride through each anchor
    tensor_slice = tf.slice(in_tensor, [0,0,0,start],[-1,-1,-1,length])
    for iStride in range(in_depth//stride-1):
        pos = stride*(iStride+1)
        tensor_slice = tf.concat([tensor_slice,
                                 tf.slice(in_tensor,
                                        [0,0,0,start+pos],
                                        [-1,-1,-1,length])],3)
    return tensor_slice

def delta_loss(act_tensor, deltas, masks, N_obj):
    '''
        Takes the activation volume from the squeezeDet layer, slices out the
        deltas from position 0 to 4*k.
        These are then unrolled into a [x*y*k, 4] list of deltas and compared to
        ground truths with a simple vector norm. The list is filtered using
        the masks, multiplying all but the main anchor at every grid point by 0.

        Input:  act_tensor: The entire activation volume
                                        [batch, X, Y, stride].
                deltas: Ground truth deltas. [batch, X*Y*ANCHOR_COUNT,4]

                masks: Binary masks indicating the anchor with
                maximum IOU for every grid point. [batch, X*Y*ANCHOR_COUNT,1]
                N_obj: number of ground truth boxes in every image [batch,1]

        Out: Float representing the average delta loss per grid point across batch
    '''
    in_shape = act_tensor.get_shape().as_list()
    batch_size = in_shape[0]
    in_depth = in_shape[3]
    masks_unwrap = tf.squeeze(tf.reshape(masks, [batch_size,-1]))

    pred_delta = tf.slice(act_tensor, [0,0,0,0],[-1,-1,-1,4*p.ANCHOR_COUNT])
    tf.summary.histogram('predicted_delta', pred_delta)
    pred_delta = tf.reshape(pred_delta,
                            [batch_size,p.GRID_SIZE*p.GRID_SIZE*p.ANCHOR_COUNT,4])

    diff_delta = tf.norm(deltas - pred_delta, axis=2)
    filtered_diff_delta = tf.multiply(diff_delta,tf.to_float(masks_unwrap))

    delta_loss_ = tf.pow(filtered_diff_delta,2)
    normal = batch_size
    return tf.reduce_sum(delta_loss_/N_obj)/(normal)

def gamma_loss(act_tensor, gammas, masks, N_obj):
    '''
        Takes the activation volume from the squeezeDet layer, slices out the
        gammas from position 4*k to 5*k .
        These are then unrolled into a [x*y*k, 1] list of gammas and compared to
        ground truths with a simple vector norm. The list is filtered using
        the masks, multiplying all but the main anchor at every grid point by 0.

        Conj_gamma is used to punish boxes predicted that don't correspond to a
        ground truth.

        Input:  act_tensor: The entire activation volume
                                        [batch, X, Y, stride].
                gammas: Ground truth gammas. [batch, X*Y*ANCHOR_COUNT,1]

                masks: Binary masks indicating the anchor with
                maximum IOU for every grid point. [batch, X*Y*ANCHOR_COUNT,1]
                N_obj: number of ground truth boxes in every image [batch,1]

        Out: Float representing the average gamma loss per grid point across batch
    '''
    in_shape = act_tensor.get_shape().as_list()
    batch_size = in_shape[0]
    in_depth = in_shape[3]
    masks_unwrap = tf.squeeze(tf.reshape(masks, [batch_size,-1]))

    #pred_gamma = get_stepped_slice(act_tensor,p.OUT_CLASSES+4,1)
    pred_gamma = tf.sigmoid(tf.slice(act_tensor,
                            [0,0,0,4*p.ANCHOR_COUNT],
                            [-1,-1,-1,p.ANCHOR_COUNT]))
    tf.summary.histogram('predicted_gamma', pred_gamma)
    pred_gamma_flat = tf.reshape(pred_gamma,
                            [batch_size,p.GRID_SIZE*p.GRID_SIZE*p.ANCHOR_COUNT])

    diff_gamma = gammas - pred_gamma_flat
    filtered_diff_gamma = tf.pow(tf.multiply(diff_gamma,tf.to_float(masks_unwrap)),2)

    ibar = 1-masks_unwrap

    conj_gamma = tf.multiply(tf.to_float(ibar), tf.pow(pred_gamma_flat,2))\
            /(p.GRID_SIZE**2*p.ANCHOR_COUNT-N_obj)
    tf.summary.histogram('predicted_conjugate_gamma', conj_gamma)
    gamma_loss_ = p.LAMBDA_CONF_P / N_obj * filtered_diff_gamma \
                    + p.LAMBDA_CONF_N* conj_gamma
    normal = batch_size
    return tf.reduce_sum(gamma_loss_)/(normal)

def class_loss(act_tensor, classes, masks, N_obj):
    '''
        Takes the activation volume from the squeezeDet layer, slices out the
        class scores from position 5*k to the end.
        These are then unrolled into a [x*y*k, classes] list of scores and compared to
        ground truths using cross entropy. The list is filtered using
        the masks, multiplying all but the main anchor at every grid point by 0.

        Input:  act_tensor: The entire activation volume
                                        [batch, X, Y, stride].
                classes: Ground truth classes. [batch, X*Y*ANCHOR_COUNT,classes]

                masks: Binary masks indicating the anchor with
                maximum IOU for every grid point. [batch, X*Y*ANCHOR_COUNT,1]
                N_obj: number of ground truth boxes in every image [batch,1]

        Out: Float representing the average gamma loss per grid point across batch
    '''
    in_shape = act_tensor.get_shape().as_list()
    batch_size = in_shape[0]
    in_depth = in_shape[3]
    masks_unwrap = tf.to_float(tf.tile(tf.reshape(masks, [-1,1]),[1, p.OUT_CLASSES]))
    classes = tf.to_float(classes)
    gs = p.GRID_SIZE
    k = p.ANCHOR_COUNT
    #pred_class = get_stepped_slice(act_tensor, 0, p.OUT_CLASSES)
    pred_class = tf.slice(act_tensor,
                            [0,0,0,5*k],
                            [-1,-1,-1,p.OUT_CLASSES*k])
    classes_flat = masks_unwrap * tf.reshape(classes, \
            [batch_size * gs**2 * k,  p.OUT_CLASSES])
    tf.summary.histogram('predicted_classes', pred_class)

    pred_class = masks_unwrap * tf.reshape(pred_class,
            [batch_size * gs**2 * k,  p.OUT_CLASSES])

    class_loss_ = tf.losses.softmax_cross_entropy(classes_flat, pred_class)
    return tf.reduce_sum(class_loss_/N_obj)/batch_size

def delta_to_box(delta, anchor):

    """
    Takes a delta and an anchor bounding box,
     and gives the bounding box predicted.

    In: delta: N x [dx, dy, dw, dh]
        anchor: N x [x, y, w, h]

    Out: box: N x [x,y,w,h]
    """

    if delta.shape == [4]:
        delta = [delta]
    if anchor.shape == [4]:
        delta = [anchor]

    N = delta.shape[0]
    d = delta.shape[1]

    assert N == anchor.shape[0], "Delta count must equal anchor count supplied!"
    assert d == 4, "Dimension 1 of deltas must equal 4! (%s)"%d


    x = anchor[:,0] + anchor[:,2]*delta[:,0]
    y = anchor[:,1] + anchor[:,3]*delta[:,1]

    w = anchor[:,2]*np.exp(delta[:,2])
    h = anchor[:,3]*np.exp(delta[:,3])

    ret_boxes = np.zeros([N,d])
    ret_boxes[:,0] = x
    ret_boxes[:,1] = y
    ret_boxes[:,2] = w
    ret_boxes[:,3] = h

    return ret_boxes
