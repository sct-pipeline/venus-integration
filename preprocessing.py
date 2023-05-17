
import json
import os
from tqdm import tqdm
from spinalcordtoolbox.scripts import sct_deepseg_sc
from spinalcordtoolbox.scripts import sct_label_vertebrae

from spinalcordtoolbox.types import Centerline
from spinalcordtoolbox.centerline.core import ParamCenterline
from spinalcordtoolbox.centerline.core import get_centerline
from spinalcordtoolbox.image import Image

def read_dataset(fname_json = 'configuration.json', path_config_file = '.'):
    """
    This function reads a json file that describes the dataset and raises an exception if a file is missing 
        or if required fields are missing from the json file.
    :param fname_json: path + file name to json description file.
    :return: a dictionary with all the fields contained in the json file.
    """

    if not os.path.isfile(path_config_file + '/' + fname_json):
        raise ValueError('File ' + fname_json + ' doesn\'t seem to exist. Please check your data.')

    with open(fname_json) as data_file:
        dataset_info = json.load(data_file)

    dataset_temp = {}
    for key in dataset_info:
        dataset_temp[str(key)] = dataset_info[key]
    dataset_info = dataset_temp

    error = ''

    # check if required fields are in json file
    if 'path_data' not in dataset_info:
        error += 'Dataset info must contain the field \'path_data\'.\n'
    if 'subjects' not in dataset_info:
        error += 'Dataset info must contain a list of subjects.\n'
    if 'data_type' not in dataset_info:
        error += 'Dataset info must contain the field \'data_type\'.\n'
    if 'suffix_image' not in dataset_info:
        error += 'Dataset info must contain the field \'suffix_image\'.\n'
    if 'contrast' not in dataset_info:
        error += 'Dataset info must contain the field \'contrast\'.\n'

    # check if path to data exist
    if not os.path.isdir(dataset_info['path_data']):
        error += 'Path to data (field \'path_data\') must exist.\n'

    # check if there are missing inputs
    for subj in dataset_info['subjects'].split(', '):
        path = dataset_info['path_data'] + '/' + subj + '/' + dataset_info['data_type'] + '/' + subj + dataset_info['suffix_image'] + '.nii.gz'
        if not os.path.isfile(path): error += f"Input for subject {subj} does not exist here: {path}"

    # if there are some errors, raise an exception
    if error != '':
        raise ValueError('JSON file containing dataset info is incomplete:\n' + error)

    return dataset_info

def segment_sc(dataset_info, regenerate = False):
    """
    This function labels the spinal cord in your image using sct_deep_seg and outputs the segmentation (binary mask) in BIDS format.
    This function also makes sure the user has performed their quality control before moving on to the next step.
    :param dataset_info: configuration file loaded into dictionary by read_dataset function.
    :param regenerate: by default, the spinal cord segmentation will not be regenerated if it already exists.
    """

    # quality control (QC) output directory
    ofolder_qc = dataset_info['path_data'] + '/derivatives/labels/qc_segment_sc'
    if not os.path.exists(ofolder_qc): os.makedirs(ofolder_qc)
    qc_complete = False

    tqdm_bar = tqdm(total = len(dataset_info['subjects'].split(', ')), unit = 'B', unit_scale = True, desc = "Status", ascii = True)
    
    for subject in dataset_info['subjects'].split(', '):

        # output directory
        ofolder = dataset_info['path_data'] + '/derivatives/labels/' + subject + '/' + dataset_info['data_type']
        if not os.path.exists(ofolder): os.makedirs(ofolder)

        # file names
        fname_image = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        fname_image_seg = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        
        # label spinal cord if it does not exists or if you want to regenerate it:
        if regenerate or not os.path.exists(fname_image_seg): 
            print(f'Generating spinal cord mask for subject {subject} here: {ofolder}')
            sct_deepseg_sc.main(['-i', fname_image, '-c', dataset_info['contrast'], '-o', fname_image_seg, '-qc', ofolder_qc])
        else:
            print(f'Spinal cord label for subject {subject} already exists!\n')
            qc_complete = True
        tqdm_bar.update(1)
    tqdm_bar.close()
    
    # checkpoint: making sure user quality controls the outputs before the pipeline moves on to the next step!
    print('Label quality control found here: ' + ofolder_qc + '/index.html\n')
    while not qc_complete: 
        user_input = input('Did you quality control the data? [Y]es/[N]o: ')
        if user_input in ['Y', 'yes', 'Yes', 'y']: qc_complete = True

def label_vertebrae(dataset_info, regenerate = False):
    """
    This function labels the intervertebral discs along the spinal cord and outputs the labels in BIDS format.
    If the intervertebral discs were manually corrected, make sure that they follow the correct naming convention.
    This function also makes sure the user has performed their quality control before moving on to the next step.
    :param dataset_info: configuration file loaded into dictionary by read_dataset function.
    :param regenerate: by default, the spinal cord segmentation will not be regenerated if it already exists.
    """

    # quality control (QC) output directory
    ofolder_qc = dataset_info['path_data'] + '/derivatives/labels/qc_label_vertebrae'
    if not os.path.exists(ofolder_qc): os.makedirs(ofolder_qc)
    qc_complete = False

    tqdm_bar = tqdm(total = len(dataset_info['subjects'].split(', ')), unit = 'B', unit_scale = True, desc = "Status", ascii = True)
    
    for subject in dataset_info['subjects'].split(', '):

        # output directory
        ofolder = dataset_info['path_data'] + '/derivatives/labels/' + subject + '/' + dataset_info['data_type']
        if not os.path.exists(ofolder): os.makedirs(ofolder)

        # file names
        fname_image = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        fname_image_seg = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        fname_image_discs = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg_labeled_discs.nii.gz'

        # label spinal cord if it does not exists or if you want to regenerate it:
        if regenerate or not os.path.exists(fname_image_discs):
            print(f'Generating vertebral levels and intervertebral disc labels for subject {subject} here: {ofolder}')
            sct_label_vertebrae.main(['-i', fname_image, '-s', fname_image_seg, '-c', dataset_info['contrast'], '-ofolder', ofolder, '-qc', ofolder_qc])
        else:
            print(f'Spinal cord label for subject {subject} already exists!\n')
            qc_complete = True
        tqdm_bar.update(1)
    tqdm_bar.close()

    # checkpoint: making sure user quality controls the outputs before the pipeline moves on to the next step!
    print('Label quality control found here: ' + ofolder_qc + '/index.html\n')
    while not qc_complete: 
        user_input = input('Did you quality control the data? [Y]es/[N]o: ')
        if user_input in ['Y', 'yes', 'Yes', 'y']: qc_complete = True

def label_centerline(dataset_info, param_centerline, regenerate = False):
    """
    This function labels the spinal cord centerline and outputs the centerline as .npz and .nii.gz according to BIDS format.
    :param dataset_info: configuration file loaded into dictionary by read_dataset function.
    :param regenerate: by default, the spinal cord segmentation will not be regenerated if it already exists.
    """

    list_centerline = []

    tqdm_bar = tqdm(total = len(dataset_info['subjects'].split(', ')), unit = 'B', unit_scale = True, desc = "Status", ascii = True)

    for subject in dataset_info['subjects'].split(', '):

        # output directory
        ofolder = dataset_info['path_data'] + '/derivatives/labels/' + subject + '/' + dataset_info['data_type']
        if not os.path.exists(ofolder): os.makedirs(ofolder)

        # file names
        fname_image = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        fname_image_seg = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        fname_image_discs = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg_labeled_discs.nii.gz'
        fname_centerline = ofolder + '/' + subject + dataset_info['suffix_image'] + '_centerline'

        # if centerline exists, we load it, if not, we compute it
        if os.path.isfile(fname_centerline + '.npz') and not regenerate:
            print("Centerline for " + subject + " exists and will not be recomputed!")
            centerline = Centerline(fname = fname_centerline + '.npz')
        else:
            if os.path.isfile(fname_image_seg):
                print(subject + ' spinal cord segmentation exists. Extracting centerline from ' + fname_image_seg)
                im_seg = Image(fname_image_seg).change_orientation('RPI')
            else:
                print(subject + ' spinal cord segmentation does not exist. Extracting centerline from ' + fname_image)
                im_seg = Image(fname_image).change_orientation('RPI')

            # extracting intervertebral discs
            im_discs = Image(fname_image_discs).change_orientation('RPI')
            coord = im_discs.getNonZeroCoordinates(sorting = 'z', reverse_coord = True)
            coord_physical = []
            for c in coord:
                c_p = list(im_discs.transfo_pix2phys([[c.x, c.y, c.z]])[0])
                c_p.append(c.value)
                coord_physical.append(c_p)

            # extracting centerline
            im_ctl, arr_ctl, arr_ctl_der, _ = get_centerline(im_seg, param = param_centerline, space = 'phys')

            # save centerline as .nii.gz file
            im_ctl.save(fname_centerline + '.nii.gz', dtype = 'float32')
            centerline = Centerline(points_x = arr_ctl[0], points_y = arr_ctl[1], points_z = arr_ctl[2], deriv_x = arr_ctl_der[0], deriv_y = arr_ctl_der[1], deriv_z = arr_ctl_der[2])
            centerline.compute_vertebral_distribution(coord_physical)
            
            # save centerline .npz file
            centerline.save_centerline(fname_output = fname_centerline)
        list_centerline.append(centerline)
        tqdm_bar.update(1)
    tqdm_bar.close()