[![Abcdspec-compliant](https://img.shields.io/badge/ABCD_Spec-v1.1-green.svg)](https://github.com/brain-life/abcd-spec)
[![Run on Brainlife.io](https://img.shields.io/badge/Brainlife-bl.app.444-blue.svg)](https://doi.org/10.25663/bl.app.444)

# QSMxT-Brainlife

This is the Brainlife App implementation of [QSMxT](https://qsmxt.github.io/) - an end-to-end software toolbox for Quantitative Susceptibility Mapping (QSM) that automatically reconstructs and processes large datasets in parallel using sensible defaults. See the [QSMxT Brainlife App](https://brainlife.io/app/64805d03b10869ed4e857e2e) page here.

## What is QSM?

QSM is a form of quantitative MRI that aims to measure the magnetic susceptibility of objects. Susceptibility maps are derived by post-processing the phase component of the complex MRI signal, usually from a 3D gradient-echo (3D-GRE) acquisition. QSM has many applications, mostly in human brain imaging of conditions such as traumatic brain injuries, neuroinflammatory and neurodegenerative diseases, ageing, tumours, with emerging applications across the human body and in animals.

## Inputs

The QSMxT Brainlife App takes a [`magphase`](https://brainlife.io/datatype/64792b1c79d13f6418e4fb75) datatype as input, which includes both the magnitude and phase components of an MRI acquisition as NIfTI files, and associated JSON sidecars. For multi-echo acquisitions, echoes should be combined along the 4th dimension of the image volumes, with JSON files combined as elements of a list within a root "echoes" object. 

## Outputs

The QSMxT Brainlife App produces a [`qsm`](https://brainlife.io/datatype/62b03ee2ab3e66978064ed79) datatype as output in NIfTI format, with voxel values measured in parts-per-million (ppm). 

### Authors
The QSMxT Brainlife App was developed by Ashley Stewart, with a wider group contributing to the underlying [QSMxT toolbox](https://github.com/QSMxT/QSMxT/graphs/contributors) and [original publication](https://doi.org/10.1002/mrm.29048).

#### Copyright (c) 2022 brainlife.io The University of Texas at Austin

### Funding Acknowledgement
brainlife.io is publicly funded by the following:

[![NSF-BCS-1734853](https://img.shields.io/badge/NSF_BCS-1734853-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1734853)
[![NSF-BCS-1636893](https://img.shields.io/badge/NSF_BCS-1636893-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1636893)
[![NSF-ACI-1916518](https://img.shields.io/badge/NSF_ACI-1916518-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1916518)
[![NSF-IIS-1912270](https://img.shields.io/badge/NSF_IIS-1912270-blue.svg)](https://nsf.gov/awardsearch/showAward?AWD_ID=1912270)
[![NIH-NIBIB-R01EB029272](https://img.shields.io/badge/NIH_NIBIB-R01EB029272-green.svg)](https://grantome.com/grant/NIH/R01-EB029272-01)

### Citations
1. Stewart, A. W., Robinson, S. D., O’Brien, K., Jin, J., Widhalm, G., Hangel, G., ... & Bollmann, S. (2022). QSMxT: Robust masking and artifact reduction for quantitative susceptibility mapping. Magnetic resonance in medicine, 87(3), 1289-1300. [https://doi.org/10.1002/mrm.29048](https://doi.org/10.1002/mrm.29048)
2. Avesani, P., McPherson, B., Hayashi, S. et al. The open diffusion data derivatives, brain data upcycling via integrated publishing of derivatives and reproducible open cloud services. Sci Data 6, 69 (2019). [https://doi.org/10.1038/s41597-019-0073-y](https://doi.org/10.1038/s41597-019-0073-y)


## Running the App 

### On Brainlife.io

You can find QSMxT at [brainlife.io](https://brainlife.io/) and execute it via the "Execute" tab.

### Running Locally (on your machine)

1. git clone this repo.
2. Inside the cloned directory, create `config.json` with something like the following content with paths to your input files. For multi-echo data, you may use multiple elements in the `mag`, `phase`, `mag-json`, and `phase-json` lists. Alternatively, you may use a single 4D NIfTI volume for the `.nii` inputs and a single JSON file for the `.json` files, with each sidecar object stored as an element in a root `echoes` key:

```json
{
    "mag": ["magphase/mag.nii"],
    "phase": ["magphase/phase.nii"],
    "mag-json": ["magphase/mag.json"],
    "phase-json": ["magphase/phase.json"],
    "premade": "gre"
}
```

3. Launch the App by executing `main`

```bash
./main
```

### Sample Datasets

If you don't have your own input files, you can generate them using the [`qsm-forward`](https://github.com/astewartau/qsm-forward) package, which conveniently exists in Brainlife App form via the [QSM Data Generator](https://github.com/astewartau/qsm-forward-brainlife) Brainlife App. 

```
npm install -g brainlife
bl login
mkdir input
bl dataset download 5a0f0fad2c214c9ba8624376#5a050966eec2b300611abff2 && mv 5a0f0fad2c214c9ba8624376#5a050966eec2b300611abff2 .
```

## Output

All output file (a resampled T1w NIFTI-1 file) will be generated inside the current working directory (pwd), inside a specifc directory called:

```
out_dir
```

### Dependencies

This App requires `curl` and `singularity` to run.

