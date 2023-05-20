
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
    Class to represent point-normal plane (that can be written to and from a .json file)
    :param origin: list [x, y, z] with origin coordinates (float or int)
    :param normal: list [a, b, c] with normal components (float or int)
    :param orientation: 3-character string (e.g. 'RAS','LPS','LPI')
    :param filename: string ending in .json
    :param space: 'pix' = pixel space, 'phys' = physical space / native.
    """
    def __init__(self, origin, normal, orientation, space = 'pix'):
        self.origin = origin
        self.normal = normal
        self.orientation = orientation
        self.space = space

    @classmethod
    def fromJsonFile(cls,filename):
        with open(filename, "r") as f: data = f.read()
        dict_tmp = json.loads(data)
        return(pointNormalPlane(origin = dict_tmp['origin'], normal = dict_tmp['normal'],
            orientation = dict_tmp['orientation'], space = dict_tmp['space']))

    def write_plane_json(self,filename):
        new_plane_dict_json = json.dumps(self.__dict__)
        if (filename.endswith('json')):
            with open(filename, "w") as f: f.write(new_plane_dict_json)
        else:
            with open(f'{filename}.json', "w") as f: f.write(new_plane_dict_json)

def get_orthog_plane(im, ctl, iz, orient_dest = 'RAS'):
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

    im = im.change_orientation('RPI')
    # Next 5 lines from from spinalcordtoolbox.process_seg import compute_shape
    _, _, _, _, px, py, pz, _ = im.dim
    # Extract tangent vector to the centerline (i.e. its derivative)
    tangent_vect = np.array([ctl.derivatives[iz][0] * px, ctl.derivatives[iz][1] * py, pz])
    # Normalize vector by its L2 norm
    norm = list(tangent_vect / np.linalg.norm(tangent_vect))
    
    # Find origin in physical space, RAS orientation (for SCT slicer)
    # origin_pix_RPI = list(ctl.get_point_from_index(iz))
    # origin_pix_orient_dest = list(Coordinate(origin_pix_RPI).permute(im, orient_dest = orientation))
    # origin_phys_orient_dest = list(im.change_orientation(orientation).transfo_pix2phys([origin_pix_orient_dest])[0])
    
    phys_RPI = Coordinate(list(ctl.points[iz]))
    phys_dest = list(phys_RPI.permute(im, orient_dest = orient_dest))

    # Return object of class pointNormalPlane
    return(pointNormalPlane(origin = list(phys_dest), normal = norm, orientation = orient_dest, space = 'phys'))

def slice_select(dataset_info, list_centerline, upper_disc_number, lower_disc_number, n_slices, slicer_markup = True):
    """
    Function to compute the z-indices (in SCT image space) of N slices that are equidistant along the centerline
    and output a point-normal plane that is orthogonal to the centerline at each slice of interest

    :param image: anatomical image (e.g. t2.nii.gz)
    :param image_seg: spinal cord segmentation of image (e.g. t2_seg.nii.gz)
    :param image_boundary: labels  of vertebra between which the N slices are to be qcomputed (e.g. t2_boundary.nii.gz)
    :param image_contrast: string (e.g. t1, t2)
    :param N_slices: int
    :return: generic point-normal plane .json file and point-normal plane markup .json file that can be read by 3D slicer
    """

    for i, subject in enumerate(dataset_info['subjects'].split(', ')):

        current_centerline = list_centerline[i]

        # upper and lower disc labels
        upper_disc_label = current_centerline.regions_labels[upper_disc_number]
        lower_disc_label = current_centerline.regions_labels[lower_disc_number]

        # upper and lower disc indices
        upper_disc_index = current_centerline.index_disc[upper_disc_label]
        lower_disc_index = current_centerline.index_disc[lower_disc_label]

        # make output directory if does not exist
        ofolder = dataset_info['path_data'] + '/derivatives/sct_slice_select/' + subject + '/' + dataset_info['data_type'] + '/' + upper_disc_label + '_to_' + lower_disc_label + '-' + str(n_slices) + '_slices'
        if not os.path.exists(ofolder): os.makedirs(ofolder)

        ######### TESTING various properties #########
        # for i in range(10):
        #     disc_label = current_centerline.regions_labels[i+1]
        #     disc_index = current_centerline.index_disc[disc_label]
        #     print(f'disc_label: {disc_label}')
        #     print(f'disc_index: {disc_index}')
        #     print(f'current_centerline.points[disc_index]: {current_centerline.points[disc_index]}')
        #     print(f'current_centerline.dist_points[disc_index]: {current_centerline.dist_points[disc_index]}')
        ##############################################

        ######### TESTING various properties #########
        # print(f'\nupper disc: {upper_disc_label}, index {upper_disc_index}')
        # print(f'current_centerline.incremental_length[upper_disc_index]: {current_centerline.incremental_length[upper_disc_index]}')
        # print(f'\nlower disc: {lower_disc_label}, index {lower_disc_index}')
        # print(f'current_centerline.incremental_length[lower_disc_index]: {current_centerline.incremental_length[lower_disc_index]}\n')
        ##############################################

        # lists to be filled by the loop below
        slice_indices = []
        interslice_dist = []

        # original distance between the upper boundary (upper disc) and lower boundary (lower disc)
        dist_btw_bounds = current_centerline.incremental_length[upper_disc_index] - current_centerline.incremental_length[lower_disc_index]
        curr_index = upper_disc_index
        slice_indices.append(curr_index)

        # writing file that saves extra information as a sanity check
        f = open(ofolder + '/slice_select_info.txt', 'w')
        
        for j in range(n_slices - 1):

            dist_btw_slices = dist_btw_bounds / (n_slices - 1 - j)

            f.write(f"\nIteration j: {j}\nCurrent index: {curr_index}\nCurrent distance between boundaries: {dist_btw_bounds}\n" + 
                f"Ideal distance between {n_slices - j} remaining slices: {dist_btw_slices}\n\n")
                        
            dist_upper = 0
            while (dist_upper < dist_btw_slices) and (curr_index >= 0):
                dist_upper += current_centerline.progressive_length[curr_index]
                curr_index -= 1
            dist_lower = dist_upper - current_centerline.progressive_length[curr_index + 1]
            
            if j == n_slices - 2: 
                slice_indices.append(lower_disc_index)
                interslice_dist.append(current_centerline.progressive_length[lower_disc_index] - interslice_dist[j-1])
            elif (abs(dist_upper - dist_btw_slices) < abs(dist_lower - dist_btw_slices)):
                slice_indices.append(curr_index)
                interslice_dist.append(dist_upper)
            else:
                slice_indices.append(curr_index - 1)
                curr_index = curr_index - 1
                interslice_dist.append(dist_lower)
       
            dist_btw_bounds =  dist_btw_bounds - dist_btw_slices

        f.write(f"\n========== Final lists ==========\n\nList of slices indices along z: {slice_indices}\n\n\n" +
            f"List of interslices distances along the centerline: {interslice_dist}\n\n\n")
        f.close()

        # Find planes orthogonal to the indices of the `slice_indices` list
        slice_indices = np.array(slice_indices)
        fname_image = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        im = Image(fname_image)
        orient_dest = 'RPI'
        for iz in slice_indices:

            phys = list(current_centerline.points[iz])
            # phys_RAS = list(phys_RPI.permute(im.change_orientation('RPI'), orient_dest = 'RPI')) ###### DELETE
            #plane_slice = pointNormalPlane(phys_RAS, [0,0,1], 'RPI', space = 'phys') ###### DELETE
            plane_slice = pointNormalPlane(phys, [0,0,1], orient_dest, space = 'phys')
            plane_slice.write_plane_json(ofolder + f"/plane_slice_{orient_dest}_{str(iz)}.json")
            if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script modules/write_slicer_markup_json.py {ofolder}/markup_plane_slice_{orient_dest}_{str(iz)}.json {plane_slice.origin[0]} {plane_slice.origin[1]} {plane_slice.origin[2]} {plane_slice.normal[0]} {plane_slice.normal[1]} {plane_slice.normal[2]}')

            plane_orthog = get_orthog_plane(im, current_centerline, iz, orient_dest)
            plane_orthog.write_plane_json(ofolder + f"/plane_orthog_{orient_dest}_{str(iz)}.json")
            if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script modules/write_slicer_markup_json.py {ofolder}/markup_plane_orthog_{orient_dest}_{str(iz)}.json {plane_orthog.origin[0]} {plane_orthog.origin[1]} {plane_orthog.origin[2]} {plane_orthog.normal[0]} {plane_orthog.normal[1]} {plane_orthog.normal[2]}')
