#!/bin/bash

if [[ $# -ne 4 ]]; then
	echo 'Usage: ./sct_plane_select.sh img.nii.gz contrast upper_vert lower_vert'
    exit
fi

input_img=$1
contrast=$2
upper_vert=$3
lower_vert=$4

cd data

# Label SC (w/ deep learning, instead of sct_prop_seg)
sct_deepseg_sc -i $input_img -c $contrast -o $(basename $input_img .nii.gz)_seg.nii.gz

# label vertebrae & disks
sct_label_vertebrae -i $input_img -s $(basename $input_img .nii.gz)_seg.nii.gz -c $contrast

# select area we want to work with (ex: from mid-vertebrum C2 to mid-vertebrum C5)
sct_label_utils -i $(basename $input_img .nii.gz)_seg_labeled.nii.gz -vert-body $upper_vert,$lower_vert -o $(basename $input_img .nii.gz)_boundary.nii.gz

