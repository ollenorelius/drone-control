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
