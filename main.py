#!/usr/bin/env python

# set up environment
print("[INFO] Importing Python modules")

import json
import os
import shutil
import glob
from qsmxt.scripts.qsmxt_functions import sys_cmd

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

# Check if all keys exist
keys = ['mag', 'phase', 'mag-json', 'phase-json']
if not all(key in config_json for key in keys):
    raise KeyError("Not all required keys found in the configuration.")

# Check if all lengths are equal
lengths = [len(config_json[key]) for key in keys]
if not all(length == lengths[0] for length in lengths):
    raise RuntimeError("The number of input files must be equal for 'mag', 'phase', 'mag-json', and 'phase-json'.")

# setup filepattern
if lengths[0] == 1:
	suffix = 'T2starw'
	file_pattern = "sub-1_ses-1_run-1_part-{part}_{suffix}.{ext}"
else:
	suffix = 'MEGRE'
	file_pattern = "sub-1_ses-1_run-1_echo-{TE_idx}_part-{part}_{suffix}.{ext}"

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
	shutil.copy(mag_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part="mag", suffix=suffix, ext="nii")))
	shutil.copy(phs_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part="phase", suffix=suffix, ext="nii")))
	shutil.copy(mag_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part="mag", suffix=suffix, ext="json")))
	shutil.copy(phs_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part="phase", suffix=suffix, ext="json")))

print("[INFO] Running nifti-convert...")
sys_cmd(cmd=f"nifti-convert {in_dir} {bids_dir} --qsm_protocol_patterns '*' --auto_yes")
print("[INFO] Running qsmxt")
sys_cmd(cmd=f"qsmxt {bids_dir} {qsm_dir} --premade {config_json['premade']} --auto_yes")

qsm_files = glob.glob(os.path.join(qsm_dir, "qsm_final", "**", "*"))

print("[INFO] Copying QSM files to output directory...")
for qsm_file in qsm_files:
	shutil.copy(qsm_file, os.path.join(out_dir, "qsm.nii"))

