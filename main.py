#!/usr/bin/env python

print("[INFO] Importing modules...")

import json
import os
import shutil
import uuid
import glob

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
if not all(key in config_json for key in ['phase', 'magnitude']):
    raise KeyError("Missing required keys: 'phase' or 'magnitude'")

print("[INFO] Checking for subjects...")
subject_rand = str(uuid.uuid4()).replace("-", "")
subjects = list({
    input_entry.get('meta', {}).get("subject") or subject_rand 
    for input_entry in config_json.get('_inputs', [])
})
if len(subjects) > 1:
    raise RuntimeError("Multiple subjects found! This App can only process one at a time.")

# Base directory: assuming this is the parent directory where the "task_id" directories are located
base_directory = os.path.abspath("..")

# find and collect file names and metadata
mag_files = []
phs_files = []
for input_entry in config_json.get('_inputs', []):
    if input_entry.get('id') in ['magnitude', 'phase']:
        task_id = input_entry.get('task_id')
        subdir = input_entry.get('subdir')
        file_path = os.path.join(base_directory, task_id, subdir, 't2starw.nii')
        if not os.path.isfile(file_path):
            raise RuntimeError(f"File {file_path} specified by config.json not found!")

        meta = input_entry.get("meta", {})
        tags = input_entry.get("tags", [])
        datatype_tags = input_entry.get("datatype_tags", [])
        subject = meta.get("subject") or subject_rand
        session = meta.get("session")
        echo = meta.get("echo")
        suffix = "MEGRE" if echo else "T2starw"

        if "part-mag" in datatype_tags:
            part = "mag"
            mag_files.append((file_path, subject, session, echo, part, suffix, meta))
        elif "part-phase" in datatype_tags:
            part = "phase"
            phs_files.append((file_path, subject, session, echo, part, suffix, meta))
        else:
            raise ValueError(f"Missing required 'part-mag' or 'part-phase' tag in input entry: {input_entry}")

if len(mag_files) != len(phs_files):
    raise RuntimeError(f"Number of magnitude files ({len(mag_files)}) must equal number of phase files ({len(phs_files)})!")

# Second loop: Copy the files and write the JSON metadata
for file_info in mag_files + phs_files:
    file_path, subject, session, echo, part, suffix, meta = file_info

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
qsm_files = [qsm_file for qsm_file in qsm_files if 'desc-singlepass' not in qsm_file]

if len(qsm_files) == 0:
    raise RuntimeError(f"No QSM files found in output directory {os.path.join(qsm_dir, 'qsm')}!")
if len(qsm_files) > 1:
    raise RuntimeError(f"Multiple QSM files found in output directory {os.path.join(qsm_dir, 'qsm')}!")

print("[INFO] Copying QSM files to output directory...")
for qsm_file in qsm_files:
    if qsm_file.endswith(".gz"):
        sys_cmd(f"gunzip {qsm_file}", print_output=True, raise_exception=True).strip()
        qsm_file = qsm_file[:-3]

    print(f"[INFO] Copying {qsm_file} to {os.path.join(out_dir, f'qsm.nii')}")
    shutil.copy(qsm_file, os.path.join(out_dir, f"qsm.nii"))

shutil.copy(sorted(phs_files)[0][0].replace('.nii.gz', '.nii').replace('.nii', '.json'), os.path.join(out_dir, f"qsm.json"))

