#!/bin/bash

for dir in output/*/test*slices
do
	cd $dir
	for file in plane*RAS_*json
	do 
		if [ ! -f markup_$(basename $file) ]; then
			echo "markup_$(basename $file) does not exist!"
			/Applications/Slicer.app/Contents/MacOS/Slicer --no-splash --no-main-window --python-script ../../../fix_slicer_markup.py $file
		fi
	done
	cd ../../..
done
