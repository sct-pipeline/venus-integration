
# Load Packages
import sys
import os
NEAR_ZERO_THRESHOLD = 1e-6
import json
from spinalcordtoolbox.image import Image
from skimage import transform
from spinalcordtoolbox.centerline.core import find_and_sort_coord, ParamCenterline, get_centerline, FitResults
import numpy as np
from spinalcordtoolbox.types import Centerline, Coordinate

class pointNormalPlane(object):
    """
    Class to represent point-Normal plane (that can be written to and from a .json file)

    :param origin: list [x,y,z] with origin coordinates (float or int)
    :param normal: list [a,b,c] with normal components (float or int)
    :param orientation: 3-character string (e.g. 'RAS','LPS','LPI')
    :param filename: string ending in .json
    :param space: 'SCT_image' or 'anatomical'
    """
    def __init__(self,origin,normal,orientation,space='SCT_image'):
        self.origin = origin
        self.normal = normal
        self.orientation = orientation
        self.space = space

    @classmethod
    def fromJsonFile(cls,filename):
        with open(filename, "r") as f:
            data=f.read()
        dict_tmp=json.loads(data)
        return(pointNormalPlane(origin=dict_tmp['origin'],normal=dict_tmp['normal'],orientation=dict_tmp['orientation'],space=dict_tmp['space']))

    def write_plane_json(self,filename):
        new_plane_dict_json = json.dumps(self.__dict__)
        if (filename.endswith('json')):
            with open(filename, "w") as f:
                f.write(new_plane_dict_json)
        else:
            with open(f'{filename}.json', "w") as f:
                f.write(new_plane_dict_json)

