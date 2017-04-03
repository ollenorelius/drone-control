IMAGE_SIZE = 256
IMAGE_CHANNELS = 3

OUT_CLASSES = 2 #Classes to recognize. 9 for KITTI
OUT_COORDS = 4 #Coordinates, for a box in 2D we need 4.
OUT_CONF = 1 #Number of confidence scores per box. Will always be one, but written out for transparecy

GRID_SIZE = 8 #Number of grid points in which to put anchors in the image.
# ^MUST MATCH FINAL ACTIVATION SIZE!
# ^^ This is in one dimension, so final size is [batch,GRID_SIZE, GRID_SIZE,depth]

ANCHOR_COUNT = 9 #Number of anchors. Must match below.

ANCHOR_SIZES = [[0.8, 0.8], [0.4, 0.8], [0.8, 0.4],
                [0.4, 0.4], [0.2, 0.4], [0.4, 0.2],
                [0.2, 0.2], [0.1, 0.2], [0.2, 0.1]]
                #Anchor sizes. [w,h] in relative units

LAMBDA_CONF_P = 75 #Param for weight of used confidence scores
LAMBDA_CONF_N = 100 #Param for punishing unused confidence scores (pushing to 0).
LAMBDA_BBOX = 5 # Param weighting in bounding box regression (delta_loss)
