# venus-integration
Code to process data for integrating acquisition planning with VENUS

## How?

### Dataset structure
The dataset should be arranged according to the BIDS convention. Using the two examples subjects listed in the `configuration.json` template file, this would be as follows:
```
dataset/
└── dataset_description.json
└── participants.tsv  <-------------------------------- Metadata describing subjects attributes e.g. sex, age, etc.
└── sub-01  <------------------------------------------ Folder enclosing data for subject 1
└── sub-02
└── sub-03
    └── anat <----------------------------------------- `anat` can be replaced by the value of `data_type` in configuration.json
        └── sub-03_T1w.nii.gz  <----------------------- MRI image in NIfTI format; `_T1w` can be replaced by the value of `suffix_image` in configuration.json
        └── sub-03_T1w.json  <------------------------- Metadata including image parameters, MRI vendor, etc.
        └── sub-03_T2w.nii.gz
        └── sub-03_T2w.json
```

### Requirements
* Python: 3.8.16
* [Spinal cord toolbox](https://spinalcordtoolbox.com/user_section/installation.html) (SCT) 5.8 in development mode commit `f0a96439dbc822136b42653e803b5f89cfa3b3ed`
* [3D Slicer](https://www.slicer.org/) 5.1.0-2022-10-20
* see `requirements.txt`

### Important files
* `configuration.json`: Modify parameters in sample `configuration.json` file provided
* `slicer_data/2022-11-16-Scene.mrml`: necessary to generate the planes as a markup file that can be read by slicer.
* `slicer_data/input-pointNormal-Plane-markup.json`: necessary to generate the planes as a markup file that can be read by slicer.

### Running
```
python pipeline.py JSON_CONFIGURATION_FILE UPPER_BOUNDARY_DISC_LABEL LOWER_BOUNDARY_DISC_LABEL N_SLICE
```

