
from preprocessing import *

# Read configuration.json to get dataset info
df_info = read_dataset(fname_json='configuration.json', path_config_file='.')

# Segment spinal cord if label does not exist
for subject in df_info['subjects'].split(', '): seg_sc(subject=subject, contrast='t1', df_info=df_info)

# Label vertebrae and discs if labels do not exist
for subject in df_info['subjects'].split(', '): label_vertebrae(subject=subject, contrast='t1', df_info=df_info)
