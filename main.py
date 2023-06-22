# Copyright (c) 2020 brainlife.io
#
# This file is a template for a python-based brainlife.io App
# brainlife stages this git repo, writes `config.json` and execute this script.
# this script reads the `config.json` and execute pynets container through singularity
#
# you can run this script(main) without any parameter to test how this App will run outside brainlife
# you will need to copy config.json.brainlife-sample to config.json before running `main` as `main`
# will read all parameters from config.json
#
# Author: Franco Pestilli
# The University of Texas at Austin

# set up environment
print("[INFO] Importing Python modules")
import json
import os
import shutil
import glob
from scripts.qsmxt_functions import sys_cmd

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

with open(config_json['phase-json'][0]) as phase_json_file_handle:
	phase_json = json.load(phase_json_file_handle)
	TE = phase_json['EchoTime']
	TE_idx = 1 if 'EchoNumber' not in phase_json else int(phase_json['EchoNumber'])
	if (('EchoTrainLength' in phase_json and int(phase_json['EchoTrainLength']) > 1) or
	   ('EchoNumber' in phase_json and int(phase_json['EchoTrainLength']) > 1)):
		suffix = 'MEGRE'
		file_pattern = "sub-1_ses-1_run-1_echo-{TE_idx}_part-{part}_{suffix}.{ext}"
	else:
		suffix = 'T2starw'
		file_pattern = "sub-1_ses-1_run-1_part-{part}_{suffix}.{ext}"

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
mag_nii_path = os.path.abspath(config_json['mag'][0])
phs_nii_path = os.path.abspath(config_json['phase'][0])
mag_json_path = os.path.abspath(config_json['mag-json'][0])
phs_json_path = os.path.abspath(config_json['phase-json'][0])

print("[INFO] Copying files to NIfTI directory...")
shutil.copy(mag_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=TE_idx, part="mag", suffix=suffix, ext="nii")))
shutil.copy(phs_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=TE_idx, part="phase", suffix=suffix, ext="nii")))
shutil.copy(mag_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=TE_idx, part="mag", suffix=suffix, ext="json")))
shutil.copy(phs_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=TE_idx, part="phase", suffix=suffix, ext="json")))

print("[INFO] Running run_1_niftiConvert.py...")
sys_cmd(cmd=f"run_1_niftiConvert.py {in_dir} {bids_dir} --t2starw_protocol_patterns '*' --auto_yes")
print("[INFO] Running run_2_qsm.py")
sys_cmd(cmd=f"run_2_qsm.py {bids_dir} {qsm_dir} --auto_yes")

qsm_files = glob.glob(os.path.join(qsm_dir, "qsm_final", "**", "*"))

print("[INFO] Copying QSM files to output directory...")
for qsm_file in qsm_files:
	shutil.copy(qsm_file, os.path.join(out_dir, "qsm.nii"))

