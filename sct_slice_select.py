
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
    def __init__(self,origin,normal,orientation,space = 'SCT_image'):
        self.origin = origin
        self.normal = normal
        self.orientation = orientation
        self.space = space

    @classmethod
    def fromJsonFile(cls,filename):
        with open(filename, "r") as f:
            data = f.read()
        dict_tmp = json.loads(data)
        return(pointNormalPlane(origin = dict_tmp['origin'],normal = dict_tmp['normal'],orientation = dict_tmp['orientation'],space = dict_tmp['space']))

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
    norm = list(tangent_vect / np.linalg.norm(tangent_vect))
    
    # Find origin in anatomical space, RAS orientation
    origin_sct_im_RPI = list(ctl.get_point_from_index(iz))
    origin_sct_im_orient_dest = list(Coordinate(origin_sct_im_RPI).permute(im.change_orientation('RPI'), orient_dest = orientation))
    origin_anat_orient_dest = list(im.change_orientation(orientation).transfo_pix2phys([origin_sct_im_orient_dest])[0])
 
    return(pointNormalPlane(origin = list(origin_anat_orient_dest), normal = norm,orientation = orientation,space = 'anatomical'))

def slice_select(dataset_info, list_centerline, upper_bound_disc_label, lower_bound_disc_label, n_slices, slicer_markup = True):
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

        # make output directory if does not exist
        ofolder = dataset_info['path_data'] + '/derivatives/sct_slice_select/' + subject + '/' + dataset_info['data_type']
        if not os.path.exists(ofolder): os.makedirs(ofolder)

        current_centerline = list_centerline[i]
        upper_label = current_centerline.regions_labels[upper_bound_disc_label]
        lower_label = current_centerline.regions_labels[lower_bound_disc_label]
        index_upper_bound_disc_label = current_centerline.index_disc[upper_label]
        index_lower_bound_disc_label = current_centerline.index_disc[lower_label]

        #print(current_centerline.labels_regions[0])
        #index_upper_bound_disc_label = current_centerline.list_labels.index(current_centerline.labels_regions[upper_bound_disc_label])
        #index_lower_bound_disc_label = current_centerline.list_labels.index(current_centerline.labels_regions[upper_bound_disc_label])

        #print(f'index_upper_bound_disc_label: {index_upper_bound_disc_label}')
        #print(f'index_lower_bound_disc_label: {index_lower_bound_disc_label}')

        # # file names
        # im_path = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        # im_seg_path = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        # im_discs_path = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg_labeled_discs.nii.gz'

        # native_orientation = Image(f'input/{im_path}').orientation
    
        # # Load anatomical files (e.g. NIFTI) into Image object and change orientation to RPI (what the SCT tools use)
        # im = Image(f'input/{im_path}').change_orientation('RPI')
        # im_seg = Image(f'output/{im_seg_path}').change_orientation('RPI')
        # im_discs = Image(f'output/{im_discs_path}').change_orientation('RPI') 

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
    #     sct_im_RPI = list(ctl.get_point_from_index(iz))
    #     sct_im_RAS = list(Coordinate(sct_im_RPI).permute(im.change_orientation('RPI'), orient_dest = 'RAS'))
    #     anat_RAS = list(im.change_orientation('RAS').transfo_pix2phys([sct_im_RAS])[0])
    #     plane_slice = pointNormalPlane(anat_RAS,[0,0,1],'RAS',space = 'anatomical')
    #     plane_slice.write_plane_json(f"output/plane_slice_RAS_{str(iz + min_z_index)}.json")
    #     if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py markup_plane_slice_RAS_{str(iz + min_z_index)}.json {plane_slice.origin[0]} {plane_slice.origin[1]} {plane_slice.origin[2]} {plane_slice.normal[0]} {plane_slice.normal[1]} {plane_slice.normal[2]}')
    #     plane_orthog = get_orthog_plane(im, ctl, arr_ctl_der,iz,min_z_index,'RAS')
    #     plane_orthog.write_plane_json(f"output/plane_orthog_RAS_{str(iz + min_z_index)}.json")
    #     if slicer_markup: os.system(f'/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script write_slicer_markup_json.py markup_plane_orthog_RAS_{str(iz + min_z_index)}.json {plane_orthog.origin[0]} {plane_orthog.origin[1]} {plane_orthog.origin[2]} {plane_orthog.normal[0]} {plane_orthog.normal[1]} {plane_orthog.normal[2]}')
    # if not os.path.exists(f"output/{image_contrast}_ctl.nii.gz"): im_centerline.change_orientation(native_orientation).save(f"output/{image_contrast}_ctl.nii.gz")
    # f.close()

# def main():
#     slices_z = slice_select(image, image_seg, image_boundary,image_contrast, N_slices,slicer_markup)

# if __name__ == "__main__":
#     image = str(sys.argv[1])
#     image_seg = str(sys.argv[2])
#     image_boundary = str(sys.argv[3])
#     image_contrast = str(sys.argv[4])
#     N_slices = int(sys.argv[5])
#     if len(sys.argv) > 6 and str(sys.argv[6]).lower() == 'false': slicer_markup = False
#     else: slicer_markup = True
#     main()

