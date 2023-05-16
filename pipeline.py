
from preprocessing import *
import sys

# Data preprocessing
dataset_info = read_dataset(sys.argv[1])
segment_sc(dataset_info)
label_vertebrae(dataset_info)