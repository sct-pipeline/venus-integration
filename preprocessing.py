
import json
import os
from spinalcordtoolbox.scripts import sct_deepseg_sc

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
    This function labels the spinal cord in your image using sct_deep_seg and outputs the segmentation in BIDS format.
    This function also makes sure the user has performed their quality control before moving on to the next step.
    :param dataset_info: configuration file loaded into dictionary by read_dataset function.
    :param regenerate: by default, the spinal cord segmentation will not be regenerated if it already exists.
    """

    qc_complete = False

    for subject in dataset_info['subjects'].split(', '):

        # output directories
        ofolder = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/' + subject + '/' + dataset_info['data_type']
        ofolder_qc = dataset_info['path_data'] + '/derivatives/sct_deepseg_sc/qc/'

        # make directories if they do not exist
        if not os.path.exists(ofolder): os.makedirs(ofolder)
        if not os.path.exists(ofolder_qc): os.makedirs(ofolder_qc)

        # file names
        im = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
        im_seg = ofolder + '/' + subject + dataset_info['suffix_image'] + '_seg.nii.gz'
        
        # label spinal cord if it does not exists or if you want to regenerate it:
        if regenerate or not os.path.exists(im_seg): 
            print(f'Generating spinal cord label for subject {subject} here: {im_seg}')
            sct_deepseg_sc.main(['-i', im, '-c', dataset_info['contrast'], '-o', im_seg, '-qc', ofolder_qc])
            print('Segmentation quality control found here: ' + ofolder_qc)
            while not qc_complete: 
                user_input = input('Did you quality control the data? [Y]es/[N]o: ')
                if user_input in ['Y', 'yes', 'Yes', 'y']: qc_complete = True
        else: print(f'Spinal cord label for subject {subject} already exists!\n')

# def label_vertebrae(subject, contrast, dataset_info, regenerate = False):
#     """
#     This function labels the spinal cord vertebral levels and intervertebral discs in BIDS format
#     If you already have these labels and their nomenclature is different, you can include the information in configuration.json
#         under 'method_label_vertebrae', 'method_label_discs', 'suffix_label_vertebrae' and 'suffix_label_discs')
#     """
    
#     # directory names
#     method_seg_sc = 'sct_deepseg_sc' if 'method_seg_sc' not in dataset_info else dataset_info['method_seg_sc']
#     method_label_vertebrae = 'sct_label_vertebrae' if 'method_label_vertebrae' not in dataset_info else dataset_info['method_label_vertebrae']
#     method_label_discs = method_label_vertebrae if 'method_label_discs' not in dataset_info else dataset_info['method_label_discs']
#     ofolder_seg_sc = dataset_info['path_data'] + '/derivatives/' + method_seg_sc + '/' + subject + '/' + dataset_info['data_type']
#     ofolder_label_vertebrae = dataset_info['path_data'] + '/derivatives/' + method_label_vertebrae + '/' + subject + '/' + dataset_info['data_type']
#     ofolder_label_discs = dataset_info['path_data'] + '/derivatives/' + method_label_discs + '/' + subject + '/' + dataset_info['data_type']
#     qc_label_vertebrae = dataset_info['path_data'] + '/derivatives/' + method_label_vertebrae + '/qc' 

#     # file names
#     suffix_seg_sc = '_seg' if 'suffix_seg_sc' not in dataset_info else dataset_info['suffix_seg_sc']
#     suffix_label_vertebrae = '_seg_labeled' if 'suffix_label_vertebrae' not in dataset_info else dataset_info['suffix_label_vertebrae']
#     suffix_label_discs = '_seg_labeled_discs' if 'suffix_label_discs' not in dataset_info else dataset_info['suffix_label_discs']
#     im = dataset_info['path_data'] + '/' + subject + '/' + dataset_info['data_type'] + '/' + subject + dataset_info['suffix_image'] + '.nii.gz'
#     im_seg = ofolder_seg_sc + '/' + subject + suffix_seg_sc + '.nii.gz'
#     im_label_vertebrae = ofolder_label_vertebrae + '/' + subject + suffix_label_vertebrae + '.nii.gz'
#     im_label_discs = ofolder_label_discs + '/' + subject + suffix_label_discs + '.nii.gz'


#     # make directories if they do not exist
#     if not os.path.exists(ofolder_label_vertebrae): os.makedirs(ofolder_label_vertebrae)
#     if not os.path.exists(ofolder_label_discs): os.makedirs(ofolder_label_discs)
#     if not os.path.exists(qc_label_vertebrae): os.makedirs(qc_label_vertebrae)

#     # label spinal cord if it does not exists or if you want to regenerate it:
#     if os.path.exists(im_label_vertebrae) and os.path.exists(im_label_discs) and not regenerate: 
#         print(f'Vertebral level & disc labels for subject {subject} already exist: {im_label_vertebrae} and {im_label_discs}!\n')
#     elif os.path.exists(im_label_discs) and not os.path.exists(im_label_vertebrae):
#         print(f'Vertebral disc labels for subject {subject} exist here: {im_label_discs}.\n Generating vertebral labels here: {im_label_vertebrae}\n')
#         sct_label_vertebrae.main(['-i',im,'-s',im_seg,'-c',contrast,'-discfile',im_label_discs,'-ofolder',ofolder_label_vertebrae,'-qc',qc_label_vertebrae])
#     else:
#         print(f'Generating vertebral level & disc labels for subject {subject} here: {ofolder_label_vertebrae}')
#         sct_label_vertebrae.main(['-i',im,'-s',im_seg,'-c',contrast,'-ofolder',ofolder_label_vertebrae,'-qc',qc_label_vertebrae])
