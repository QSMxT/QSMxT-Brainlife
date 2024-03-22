#!/usr/bin/env python

# set up environment
print("[INFO] Importing Python modules")

import json
import os
import shutil
import glob
import base64

import nibabel as nib
from matplotlib import pyplot as plt

from metrics import all_metrics
from qsmxt.scripts.sys_cmd import sys_cmd

# create necessary directories
print("[INFO] Creating directories...")

work_dir = os.path.abspath("work_dir")
in_dir = os.path.join(work_dir, "0_inputs")
bids_dir = os.path.join(work_dir, "1_bids")
qsm_dir = os.path.join(work_dir, "2_qsm")
out_dir = os.path.abspath("out_dir")
os.makedirs(work_dir, exist_ok=True)
os.makedirs(in_dir, exist_ok=True)
os.makedirs(bids_dir, exist_ok=True)
os.makedirs(qsm_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

# load inputs from config.json
print("[INFO] Loading configuration...")
with open('config.json') as config_json_file_handle:
	config_json = json.load(config_json_file_handle)

# Check if all required keys exist
keys = ['mag', 'phase', 'mag-json', 'phase-json']
if not all(key in config_json for key in keys):
	raise KeyError("Not all required keys found in the configuration.")

# Check if all lengths are equal
lengths = [len(config_json[key]) for key in keys]
if not all(length == lengths[0] for length in lengths):
	raise RuntimeError("The number of input files must be equal for 'mag', 'phase', 'mag-json', and 'phase-json'.")

# Check length of fourth dimension
length_4d = 1
with open(config_json['mag-json'][0]) as json_file:
	json_data = json.load(json_file)
	if 'echoes' in json_data:
		length_4d = len(json_data['echoes'])

# setup filepattern
if lengths[0] == 1 and length_4d == 1:
	suffix = 'T2starw'
	file_pattern = "sub-1_ses-1_run-1_part-{part}_{suffix}.{ext}"
else:
	suffix = 'MEGRE'
	file_pattern = "sub-1_ses-1_run-1_echo-{TE_idx}_part-{part}_{suffix}.{ext}"

if length_4d == 1:
	# TODO: Make this better! This information should probably be given by the brainlife datatype
	#       because JSON headers tend to be unreliable!
	if suffix == 'T2starw':
		with open(config_json['phase-json'][0]) as phase_json_file_handle:
			phase_json = json.load(phase_json_file_handle)
		phase_json['EchoNumber'] = 1
		phase_json['EchoTrainLength'] = 1
		with open(config_json['phase-json'][0], 'w') as phase_json_file_handle:
			json.dump(phase_json, phase_json_file_handle)

		with open(config_json['mag-json'][0]) as mag_json_file_handle:
			mag_json = json.load(mag_json_file_handle)
		mag_json['EchoNumber'] = 1
		mag_json['EchoTrainLength'] = 1
		with open(config_json['mag-json'][0], 'w') as mag_json_file_handle:
			json.dump(mag_json, mag_json_file_handle)

	# Load into variables predefined code inputs
	for i in range(lengths[0]):
		mag_nii_path = os.path.abspath(config_json['mag'][i])
		phs_nii_path = os.path.abspath(config_json['phase'][i])
		mag_json_path = os.path.abspath(config_json['mag-json'][i])
		phs_json_path = os.path.abspath(config_json['phase-json'][i])

		print("[INFO] Copying files to NIfTI directory...")
		print(f"[INFO] {mag_nii_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='nii'))}")
		shutil.copy(mag_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='nii')))
		print(f"[INFO] {phs_nii_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='nii'))}")
		shutil.copy(phs_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='nii')))
		print(f"[INFO] {mag_json_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='json'))}")
		shutil.copy(mag_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='json')))
		print(f"[INFO] {phs_json_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='json'))}")
		shutil.copy(phs_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='json')))
		print(f"[INFO] Input directory {in_dir} contains: {os.listdir(in_dir)}")
else:
	# Split json files
	with open(config_json['mag-json'][0]) as json_file:
		json_data = json.load(json_file)
		for i in range(len(json_data['echoes'])):
			with open(os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='json')), 'w') as mag_json_file:
				mag_json_file.write(json.dumps(json_data['echoes'][i]))
	with open(config_json['phase-json'][0]) as json_file:
		json_data = json.load(json_file)
		for i in range(len(json_data['echoes'])):
			with open(os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='json')), 'w') as mag_json_file:
				mag_json_file.write(json.dumps(json_data['echoes'][i]))
			
	# Split nifti files
	mag_nii = nib.load(config_json['mag'][0])
	phase_nii = nib.load(config_json['phase'][0])

	# Get the total number of volumes
	num_volumes = mag_nii.shape[3]

	# Loop over each volume index
	for i in range(num_volumes):
		# Get the 3D image for the current volume
		mag_3d = mag_nii.slicer[..., i]
		phase_3d = phase_nii.slicer[..., i]

		# Save the 3D image to the desired location
		nib.save(mag_3d, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='nii')))
		nib.save(phase_3d, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='nii')))

print("[INFO] Running nifti-convert...")
sys_cmd(cmd=f"nifti-convert {in_dir} {bids_dir} --auto_yes", print_output=True, raise_exception=True)
sys_cmd(cmd=f"nifti-convert {in_dir} {bids_dir} --auto_yes", print_output=True, raise_exception=True)

print("[INFO] Running qsmxt")
sys_cmd(cmd=f"qsmxt {bids_dir} {qsm_dir} --premade {config_json['premade']} --auto_yes", print_output=True, raise_exception=True)

qsm_files = glob.glob(os.path.join(qsm_dir, "qsm", "*.nii*"))  
if len(qsm_files) == 0: raise Exception(f"No QSM files found in output directory {os.path.join(qsm_dir, 'qsm')}")

print("[INFO] Copying QSM files to output directory...")
for qsm_file in qsm_files:
	shutil.copy(qsm_file, os.path.join(out_dir, "qsm.nii"))

