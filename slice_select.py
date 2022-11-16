
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

def get_orthog_plane(im, ctl, arr_ctl_der,iz,min_z_index,orientation):
    """
    Function to compute and save a point-normal plane that is orthogonal to the centerline at the slice of interest

    :param im:
    :param ctl:
    :param arr_ctl_der:
    :param iz:
    :param min_z_index:
    :param orientation:
    :return: pointNormalPlane instance
    """
    # next 5 lines from from spinalcordtoolbox.process_seg import compute_shape
    nx, ny, nz, nt, px, py, pz, pt = im.dim
    # Extract tangent vector to the centerline (i.e. its derivative)
    tangent_vect = np.array([arr_ctl_der[0][iz + min_z_index] * px, arr_ctl_der[1][iz + min_z_index] * py, pz])
    # Normalize vector by its L2 norm
    tangent_vect_norm = tangent_vect / np.linalg.norm(tangent_vect)
    
    # Find two vectors orthogonal to the tangent
    orthog_vect_1 = [-tangent_vect_norm[2],0,tangent_vect_norm[0]]
    orthog_vect_2 = [0,-tangent_vect_norm[2],tangent_vect_norm[1]]
    norm=list(np.cross(orthog_vect_1,orthog_vect_2))
    
    # Find origin in anatomical space, RAS orientation
    origin_sct_im_RPI = list(ctl.get_point_from_index(iz))
    origin_sct_im_orient_dest = list(Coordinate(origin_sct_im_RPI).permute(im.change_orientation('RPI'), orient_dest=orientation))
    origin_anat_orient_dest=list(im.change_orientation(orientation).transfo_pix2phys([origin_sct_im_orient_dest])[0])
 
    return(pointNormalPlane(origin=list(origin_anat_orient_dest), normal=norm,orientation=orientation,space='anatomical'))

