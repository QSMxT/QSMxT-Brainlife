#!/usr/bin/env python

print("[INFO] Importing modules...")

import json
import os
import shutil
import uuid
import glob
import nibabel as nib

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

# Get extra command line arguments
cli_params = config_json.get('cli-params', "")
if cli_params:
    print(f"[INFO] Found extra command line parameters: {cli_params}")

# Check if all required keys exist
print("[INFO] Checking required keys...")
keys = ['phase', 'magnitude']
if not all(key in config_json for key in keys):
    raise KeyError("Not all required keys found in the configuration.")

# Base directory: assuming this is the parent directory where the "task_id" directories are located
base_directory = os.path.abspath("..")

# choose a random subject name for any data without a subject identifier
subject_rand = str(uuid.uuid4()).replace("-", "")

# Iterate over each element in the _inputs array
for input_entry in config_json.get('_inputs', []):
    # Check if the "id" is "inputs"
    if input_entry.get('id') in ['magnitude', 'phase']:
        task_id = input_entry.get('task_id')
        subdir = input_entry.get('subdir')

        # Construct the full path to the t2starw.nii file
        file_path = os.path.join(base_directory, task_id, subdir, 't2starw.nii')

        # Ensure the file exists
        if not os.path.isfile(file_path):
            print(f"[WARNING] File not found: {file_path}")
            continue

        # Fetch required fields for renaming
        meta = input_entry.get("meta", {})
        subject = meta.get("subject") or subject_rand

        # Fetch optional fields
        session = meta.get("session")
        echo = meta.get("echo")
        suffix = "MEGRE" if echo else "T2starw"

        # Determine whether the file is magnitude or phase based on tags
        tags = input_entry.get("tags", []) + input_entry.get("datatype_tags", [])
        if "part-mag" in tags:
            part = "mag"
        elif "part-phase" in tags:
            part = "phase"
        else:
            raise ValueError(f"Missing required 'part-mag' or 'part-phase' tag in input entry: {input_entry}")

        # Construct the new filename based on available fields
        new_filename_base = f"sub-{subject}"
        if session:
            new_filename_base += f"_ses-{session}"
        if echo:
            new_filename_base += f"_echo-{echo}"
        new_filename_base += f"_part-{part}_{suffix}"

        # Construct the NIfTI destination path
        nii_dest_path = os.path.join(in_dir, new_filename_base + ".nii")

        # Copy the NIfTI file to the destination path
        print(f"[INFO] Copying {file_path} to {nii_dest_path}")
        shutil.copy(file_path, nii_dest_path)

        # Construct the JSON destination path
        json_dest_path = os.path.join(in_dir, new_filename_base + ".json")

        # Write the meta data to the destination JSON file
        print(f"[INFO] Writing meta data to {json_dest_path}")
        with open(json_dest_path, 'w') as json_file:
            json.dump(meta, json_file, indent=4)


print("[INFO] Running nifti-convert...")
sys_cmd(cmd=f"nifti-convert {in_dir} {bids_dir} --auto_yes", print_output=True, raise_exception=True)
sys_cmd(cmd=f"nifti-convert {in_dir} {bids_dir} --auto_yes", print_output=True, raise_exception=True)

print("[INFO] Running qsmxt...")
sys_cmd(cmd=f"qsmxt {bids_dir} {qsm_dir} --premade {config_json['premade']} --auto_yes {cli_params}", print_output=True, raise_exception=True)

print("[INFO] Collecting outputs...")
qsm_files_with_session = glob.glob(os.path.join(qsm_dir, "sub-*", "ses-*", "anat", "*Chimap.nii*"))
qsm_files_without_session = glob.glob(os.path.join(qsm_dir, "sub-*", "anat", "*Chimap.nii*"))
qsm_files = qsm_files_with_session + qsm_files_without_session
if len(qsm_files) == 0:
    raise RuntimeError(f"No QSM files found in output directory {os.path.join(qsm_dir, 'qsm')}")

print("[INFO] Copying QSM files to output directory...")
for qsm_file in qsm_files:
    if qsm_file.endswith(".gz"):
        sys_cmd(f"gunzip {qsm_file}", print_output=True, raise_exception=True).strip()
        qsm_file = qsm_file[:-3]

    shutil.copy(qsm_file, os.path.join(out_dir, f"qsm.nii"))

