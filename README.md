# venus-integration
Code to process data for integrating acquisition planning with VENUS

### Step 1. Preprocessing your data
Label the spinal cord, vertebrae and vertebral boundaries within which you want to compute your slices. \
Usage: ./preprocessing.sh anatomical_image.nii.gz contrast upper_vertebra upper_vertebra \
Labels (integer values) corresponding to each vertebra and disc can be found [here](https://spinalcordtoolbox.com/user_section/tutorials/registration-to-template/vertebral-labeling/labeling-conventions.html).\
```
./preprocessing.sh t2.nii.gz t2 2 5
```

### Step 2. Slice selection and orthogonal plane generation
Find the indices of N slices (N = 5 in this example) that are equidistant along the centerline. \
At each slice, compute a plane that is orthogonal to the centerline. \
```
python slice_select.py t2.nii.gz t2_seg.nii.gz t2_boundary.nii.gz t2 5
```

## Data

`data/t2.nii.gz` was downloaded from the SCT t2 single subject tutorial: https://spinalcordtoolbox.com/user_section/tutorials/segmentation/before-starting.html
`data/2022-11-16-Scene.mrml`: necessary to generate the planes as a markup file that can be read by slicer.			
`data/input-pointNormal-Plane-markup.json`: necessary to generate the planes as a markup file that can be read by slicer.	