
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
        #f.write(f"========== Slice indices along z in image space ========== \n\n")
        orient_dest = 'RPI'
        for iz in slice_indices:

            phys = list(current_centerline.points[iz])
            #phys_RAS = list(phys_RPI.permute(im.change_orientation('RPI'), orient_dest = 'RPI'))

            #plane_slice = pointNormalPlane(phys_RAS, [0,0,1], 'RPI', space = 'phys')
            plane_slice = pointNormalPlane(phys, [0,0,1], orient_dest, space = 'phys')
            plane_slice.write_plane_json(ofolder + f"/plane_slice_{orient_dest}_{str(iz)}.json")
            if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py {ofolder}/markup_plane_slice_{orient_dest}_{str(iz)}.json {plane_slice.origin[0]} {plane_slice.origin[1]} {plane_slice.origin[2]} {plane_slice.normal[0]} {plane_slice.normal[1]} {plane_slice.normal[2]}')

            plane_orthog = get_orthog_plane(im, current_centerline, iz, orient_dest)
            plane_orthog.write_plane_json(ofolder + f"/plane_orthog_{orient_dest}_{str(iz)}.json")
            if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py {ofolder}/markup_plane_orthog_{orient_dest}_{str(iz)}.json {plane_orthog.origin[0]} {plane_orthog.origin[1]} {plane_orthog.origin[2]} {plane_orthog.normal[0]} {plane_orthog.normal[1]} {plane_orthog.normal[2]}')

#print(f'phys RPI: {current_centerline.points[iz]}')
    #print(f'list(Coordinate(current_centerline.points[iz])): {list(Coordinate(list(current_centerline.points[iz])))}')
    #print(f'phys RAS: {current_centerline.points[iz]}')

    # pix_RPI = current_centerline.points[iz]#list(current_centerline.get_point_from_index(iz))
    # print(f'\npix_RPI: {pix_RPI}') ###### DELETE
    # pix_RAS = list(Coordinate(pix_RPI).permute(im.change_orientation('RPI'), orient_dest = 'RAS'))
    # print(f'\npix_RAS: {pix_RPI}') ###### DELETE
    # phys_RAS = list(im.change_orientation('RAS').transfo_pix2phys([pix_RAS])[0])
    # print(f'\npix_RAS: {phys_RAS}') ###### DELETE

    # # Get z-index in image space of lower and upper bound within which we want to obtain our N slices (use this to create z_ref within which centerline will be computed)
    # X, Y, Z = (im_boundary.data > NEAR_ZERO_THRESHOLD).nonzero()
    # min_z_index, max_z_index = min(Z), max(Z) # equiv: im_boundary.getNonZeroCoordinates()[0].z, im_boundary.getNonZeroCoordinates()[1].z
    # z_ref = np.array(range(min_z_index,max_z_index + 1))

    # # Get centerline
    # param_centerline = ParamCenterline(algo_fitting = 'optic',contrast = image_contrast) 
    # im_centerline, arr_ctl, arr_ctl_der,fit_results = get_centerline(im,param = param_centerline, verbose = 1) # ISSUE: why does fit_results output NoneType?
    
    # # Create Centerline object within min_z_index and max_z_index
    # ctl = Centerline(points_x = arr_ctl[0,z_ref],points_y = arr_ctl[1,z_ref],points_z = arr_ctl[2,z_ref], deriv_x = arr_ctl_der[0,z_ref],deriv_y = arr_ctl_der[1,z_ref],deriv_z = arr_ctl_der[2,z_ref])

    # # Find N slices that are approximately equidistant along the centerline (NOT along S-I axis!)
    # dist_between_slices = float(ctl.length/(N_slices)-1)
    # slices_z = []
    # interslice_dist = []
    # slices_z.append(0)
    # slice_i = 1
    # i = 0
    # f = open('output/info.txt', 'w')
    # f.write(f"Average distance between slices: {round(dist_between_slices,2)}\n")  # Sanity check!
    # while slice_i < N_slices:
    #     dist_upper = 0
    #     dist_lower = 0
    #     while (dist_upper < dist_between_slices) and (i < len(ctl.progressive_length)):
    #         dist_upper += ctl.progressive_length[i]
    #         i += 1
    #     dist_lower = dist_upper - ctl.progressive_length[i-1]
    #     f.write(f"Current interslice distance can range from {round(dist_lower,2)} (index {i-1}) to {round(dist_upper,2)} (index {i})\n") # Sanity check!
    #     if (abs(dist_upper-dist_between_slices) < abs(dist_lower-dist_between_slices)):
    #         slices_z.append(i)
    #         interslice_dist.append(dist_upper)
    #         f.write(f"Current centerline incremental length: {ctl.incremental_length[i]}\n")
    #     else:
    #         slices_z.append(i-1)                
    #         interslice_dist.append(dist_lower)
    #         f.write(f"Current centerline incremental length: {ctl.incremental_length[i-1]}\n")
    #     slice_i += 1
    # slices_z = np.array(slices_z)
    # f.write(f"\nIndices along z in image space: ")
    # for iz in slices_z:
    #     f.write(f"{iz} ")
    #     pix_RPI = list(ctl.get_point_from_index(iz))
    #     pix_RAS = list(Coordinate(pix_RPI).permute(im.change_orientation('RPI'), orient_dest = 'RAS'))
    #     phys_RAS = list(im.change_orientation('RAS').transfo_pix2phys([pix_RAS])[0])
    #     plane_slice = pointNormalPlane(anat_RAS,[0,0,1],'RAS',space = 'anatomical')
    #     plane_slice.write_plane_json(f"output/plane_slice_RAS_{str(iz + min_z_index)}.json")
    #     if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py markup_plane_slice_RAS_{str(iz + min_z_index)}.json {plane_slice.origin[0]} {plane_slice.origin[1]} {plane_slice.origin[2]} {plane_slice.normal[0]} {plane_slice.normal[1]} {plane_slice.normal[2]}')
    #     plane_orthog = get_orthog_plane(im, ctl, arr_ctl_der,iz,min_z_index,'RAS')
    #     plane_orthog.write_plane_json(f"output/plane_orthog_RAS_{str(iz + min_z_index)}.json")
    #     if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py markup_plane_orthog_RAS_{str(iz + min_z_index)}.json {plane_orthog.origin[0]} {plane_orthog.origin[1]} {plane_orthog.origin[2]} {plane_orthog.normal[0]} {plane_orthog.normal[1]} {plane_orthog.normal[2]}')
    # if not os.path.exists(f"output/{image_contrast}_ctl.nii.gz"): im_centerline.change_orientation(native_orientation).save(f"output/{image_contrast}_ctl.nii.gz")