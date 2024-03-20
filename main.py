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

if 'bids' in config_json:
	print(f"[INFO] BIDS input detected! Extracting {config_json['bids']} to {bids_dir}.")
	sys_cmd(f"tar xf {config_json['bids']} -C {bids_dir}")

else:
	# Check if all required keys exist
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
		print(f"[INFO] {mag_nii_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='nii'))}")
		shutil.copy(mag_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='nii')))
		print(f"[INFO] {phs_nii_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='nii'))}")
		shutil.copy(phs_nii_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='nii')))
		print(f"[INFO] {mag_json_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='json'))}")
		shutil.copy(mag_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='mag', suffix=suffix, ext='json')))
		print(f"[INFO] {phs_json_path} -> {os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='json'))}")
		shutil.copy(phs_json_path, os.path.join(in_dir, file_pattern.format(TE_idx=i+1, part='phase', suffix=suffix, ext='json')))
		print(f"[INFO] Input directory {in_dir} contains: {os.listdir(in_dir)}")


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

if 'qsm' in config_json:
	def plot_error_metrics(metrics, title="Error Metrics"):
		# Create a bar plot for the metrics
		#sns.set_theme(style='whitegrid')
		plt.figure(figsize=(10, 6))
		
		# stem function
		plt.ylim(0, 1.0)
		
		# stem function: If x is not provided, a sequence of numbers is created by python:
		plt.stem(metrics.keys(), metrics.values())

		plt.title('QSM evaluation metrics')
		plt.xlabel('Metric')
		plt.ylabel('Value')
		plt.xticks(rotation=45)
		plt.tight_layout()
    
		# Annotate each point with its value
		for key, value in metrics.items():
			plt.text(key, value + 0.01, f"{value:.3f}", 
					ha='left', va='bottom', 
					fontsize=8, rotation=0)
		
		# Save the plot as a PNG file
		plt.savefig("metrics_plot.png")
		plt.close()

	def encode_image_to_base64(image_path):
		with open(image_path, "rb") as image_file:
			encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
		return encoded_string

	def create_json_for_brainlife(encoded_image, image_title="My image title"):
		data = {
			"brainlife": [
				{
					"type": "image/png",
					"name": image_title,
					"base64": encoded_image
				}
			]
		}
		return json.dumps(data, indent=4)

	print("[INFO] Loading QSM results for metrics...")
	qsm_file = qsm_files[0]
	ground_truth_file = config_json['qsm']
	qsm = nib.load(qsm_file).get_fdata()
	ground_truth = nib.load(ground_truth_file).get_fdata()

	print("[INFO] Computing evaluation metrics...")
	metrics_dict = all_metrics(qsm, ground_truth)
	del metrics_dict['RMSE']
	metrics_dict['NRMSE'] /= 100.0
	#metrics_dict['HFEN'] 
	#metrics_dict['MAD']
	#metrics_dict['XSIM']
	metrics_dict['CC'] = (metrics_dict['CC'][0] + 1) / 2
	metrics_dict['NMI'] -= 1 
	#metrics_dict['GXE']


	print("[INFO] Generating figure...")
	plot_error_metrics(metrics_dict)

	print("[INFO] Converting figure to base64...")
	encoded_image = encode_image_to_base64("metrics_plot.png")

	print("[INFO] Generating product.json...")
	json_data = create_json_for_brainlife(encoded_image)
	with open('product.json', 'w') as json_file:
		json_file.write(json_data)
	

