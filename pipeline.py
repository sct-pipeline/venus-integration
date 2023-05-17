
from preprocessing import *
#from slice_select import *
import sys
from spinalcordtoolbox.centerline.core import ParamCenterline

# make sure user inputs are correct
if len(sys.argv) != 4:
    print('Input error. Make sure you ran `python pipeline.py JSON_CONFIGURATION_FILE UPPER_BOUNDARY_DISC_LABEL LOWER_BOUNDARY_DISC_LABEL')
    sys.exit(1)
elif not sys.argv[2].isdigit():
    print(sys.argv[2])
    print('Input error. Make sure UPPER_BOUNDARY_DISC_LABEL is of type int.')
    sys.exit(1)
elif not sys.argv[3].isdigit():
    print(sys.argv[3])
    print('Input error. Make sure LOWER_BOUNDARY_DISC_LABEL is of type int.')
    sys.exit(1)

# load json config file
dataset_info = read_dataset(sys.argv[1])

# segment spinal cord (sc)
segment_sc(dataset_info)

# label discs
label_vertebrae(dataset_info)

# extract centerline
param_centerline = ParamCenterline(algo_fitting = 'linear', contrast = dataset_info['contrast'], smooth = 50) 
label_centerline(dataset_info, param_centerline, regenerate = False)

# upper_bound_disc_label = int(sys.argv[2])
# lower_bound_disc_label = int(sys.argv[3])