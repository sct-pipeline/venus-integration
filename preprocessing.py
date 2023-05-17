
import json
import os
from spinalcordtoolbox.scripts import sct_deepseg_sc
from spinalcordtoolbox.scripts import sct_label_vertebrae

def read_dataset(fname_json = 'configuration.json', path_config_file = '.'):
    """
    This function (borrowed from https://github.com/neuropoly/template/preprocessing.py) reads a json file that describes the dataset,
     including the list of subjects as well as
    suffix for filenames (centerline, disks, segmentations, etc.).
    The function raises an exception if the file is missing or if required fields are missing from the json file.
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

    qc_complete = False
    ofolder_qc = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/qc/'

    for subject in dataset_info['subjects'].split(', '):

        # output directories
        ofolder = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/' + subject + '/' + dataset_info['data_type']

        # make directories if they do not exist
        if not os.path.exists(ofolder): os.makedirs(ofolder)
        if not os.path.exists(ofolder_qc): os.makedirs(ofolder_qc)

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
    
    # checkpoint: making sure user quality controls the outputs before the pipeline moves on to the next step!
    print('Label quality control found here: ' + ofolder_qc + '\n')
    while not qc_complete: 
        user_input = input('Did you quality control the data? [Y]es/[N]o: ')
        if user_input in ['Y', 'yes', 'Yes', 'y']: qc_complete = True

def label_vertebrae(dataset_info, regenerate = False):
    """
    This function labels the vertebral levels and intervertebral discs along the spinal cord and outputs the labels in BIDS format.
    If the intervertebral discs were manually corrected, make sure that there only exists an intervertebral disc label file
        (and delete the vertebral level file), such that the pipeline will regenerate the intervertebral level label file according
        to the corrected segmentations.
        ###### Note: we may not even need the intervertebral disc labels
    This function also makes sure the user has performed their quality control before moving on to the next step.
    :param dataset_info: configuration file loaded into dictionary by read_dataset function.
    :param regenerate: by default, the spinal cord segmentation will not be regenerated if it already exists.
    """

    qc_complete = False
    ofolder_qc = dataset_info['path_data'] + '/derivatives/sct_label_vertebrae/qc/'

    for subject in dataset_info['subjects'].split(', '):

        # output directory
        ofolder = dataset_info['path_data'] + '/derivatives/sct_label_vertebrae/' + subject + '/' + dataset_info['data_type']
        
        # make directories if they do not exist
        if not os.path.exists(ofolder): os.makedirs(ofolder)
        if not os.path.exists(ofolder_qc): os.makedirs(ofolder_qc)

        # file names
        fname_image = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        fname_image_seg = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        fname_image_discs = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg_labeled_discs.nii.gz'

        # label spinal cord if it does not exists or if you want to regenerate it:
        if regenerate or not os.path.exists(fname_image_discs):
            print(f'Generating vertebral levels and intervertebral disc labels for subject {subject} here: {ofolder}')
            sct_label_vertebrae.main(['-i', fname_image, '-s', fname_image_seg, '-c', dataset_info['contrast'], '-ofolder', ofolder, '-qc', ofolder_qc])
        else:
            print(f'Spinal cord label for subject {subject} already exists!\n')
            qc_complete = True

    # checkpoint: making sure user quality controls the outputs before the pipeline moves on to the next step!
    print('Label quality control found here: ' + ofolder_qc + '\n')
    while not qc_complete: 
        user_input = input('Did you quality control the data? [Y]es/[N]o: ')
        if user_input in ['Y', 'yes', 'Yes', 'y']: qc_complete = True
