# venus-integration
Code to process data for integrating acquisition planning with VENUS

### Step 1. create mrml scene (`slicer` is a bashrc alias for `/Applications/Slicer.app/Contents/MacOS/Slicer`)
`slicer input-pointNormal-Plane-markup.json`
Make sure to save the scene (default name but local directory, e.g. `2022-11-16-Scene.mrml`)

### Step 2. activate sct venv and fetch input file
`conda activate /Users/nadiablostein/sct_5.7/python/envs/venv_sct`
`cp ../t2.nii.gz .`

### Step 3. Label spinal cord, vertebrae and vertebral boundaries within which you want to compute your slices (e.g. C2 = '2', C5 = '5') 
`./preprocessing.sh t2.nii.gz t2 2 5`
Usage: ./sct_plane_select.sh img.nii.gz contrast upper_vert lower_vert

### Step 4. Select your N slices (equidistant along centerline) and compute their planes orthogonal to centerline
python slice_select.py t2.nii.gz t2_seg.nii.gz t2_boundary.nii.gz t2 5

