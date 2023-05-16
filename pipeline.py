
from preprocessing import *
import sys

dataset_info = read_dataset(sys.argv[1])
segment_sc(dataset_info)