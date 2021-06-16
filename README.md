Scripts and notebooks in this package should be run with python 3 (they have been tested with python 3.7). The main dependencies are:
- scipy
- numpy
- pandas
- uproot (version 4)
- scikit-learn
- xgboost

## Setup at cmslpc (for procesing data and submitting condor jobs

Setting up the CMS software and cloning the HGCAL L1 trigger simulation:
```
export SCRAM_ARCH=slc7_amd64_gcc900 
source /cvmfs/cms.cern.ch/cmsset_default.sh # (add this to .bashrc if possible)
cmsrel CMSSW_11_3_0
cd CMSSW_11_3_0/src/
cmsenv
git cms-init
git remote add pfcaldev https://github.com/PFCal-dev/cmssw.git
git fetch pfcaldev
git cms-merge-topic -u PFCal-dev:v3.23.3_1130
scram b -j4
```

Get configuration files:
```
cd L1Trigger/L1THGCalUtilities/test
wget https://github.com/cmantill/ECONAutoencoderStudy/blob/master/fragments/produce_ntuple_std_ae_xyseed_reduced_genmatch_v11_cfg.py
wget https://github.com/cmantill/ECONAutoencoderStudy/blob/master/fragments/produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py
```

Get training models:
```
cd  ../L1THGCal/data/
# copy AEmodels folder in data/ dir (latest models available at https://www.dropbox.com/s/f9rib5uyv2f0qzp/AEmodels.tgz?dl=0)
cd -
```

### Running locally
Then you can run locally, e.g.:
```
cmsRun produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py
```
This will produce a `ntuple.root` file, which will contain subdirectories, e.g. `FloatingpointAutoEncoderTelescopeMSEDummyHistomaxxydr015Genclustersntuple->cd()` , each with a TTree inside. You can get the contents of the tree with `HGCalTriggerNtuple->Show(0)`.

### Running jobs in crab/
To submit a large production you will need to run over all the files. 
You can use `crab` for this. This needs a valid GRID certificate.

The crab configuration files are e.g. [here for electrons](https://github.com/cmantill/ECONAutoencoderStudy/blob/master/fragments/eleCrabConfig.py). Make sure to change the output username.

Some example files are already produced here:
```
/eos/uscms/store/user/cmantill/HGCAL/AE_Jun11/
```

## Setup for juptyer notebooks


## Input data for physics studies

We first need to simulate the HGCAL trigger cells using the ECON-T algorithms. For this we use simulated datasets (photons, electrons, pileup).
Full documentation can be found [here](https://twiki.cern.ch/twiki/bin/viewauth/CMS/HGCALTriggerPrimitivesSimulation).
This repository is used to simulate all the ECON-T algorithms in the CMS official simulation (cmssw).

We are currently running with TPG release v3.23.3_1130.
A short history of releases is the following:
- v3.22.1. (had bug on normalization fixed by danny [here](https://github.com/PFCal-dev/cmssw/commit/65625ee12e0c1a527820d20aeaaa656cf6f4df48#diff-0003f7b8caf7041ba5afce04bcfa74b1a2593d991fc3b5b84294d5ee9e680ae4)
- v3.23.3_1130 (fixes in for AE)

### Configuration files
To run this we need configuration files. These are the following:
- For 200PU electron gun ( /SingleElectron_PT2to200/Phase2HLTTDRWinter20DIGI-PU200_110X_mcRun4_realistic_v3_ext2-v2/GEN-SIM-DIGI-RAW) and 0PU photon gun (/SinglePhoton_PT2to200/Phase2HLTTDRWinter20DIGI-NoPU_110X_mcRun4_realistic_v3-v2/GEN-SIM-DIGI-RAW):
`produce_ntuple_std_ae_xyseed_reduced_genmatch_v11_cfg.py`

- For 200PU MinBias (/MinBias_TuneCP5_14TeV-pythia8/Phase2HLTTDRWinter20DIGI-PU200_110X_mcRun4_realistic_v3-v3/GEN-SIM-DIGI-RAW/):
`produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py`

### AutoEncoder implementation 
The implementation of the AutoEncoder (AE) in CMSSW is in [HGCalConcentratorAutoEncoderImpl.cc](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc):
- The [`select` function](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc#L122-L174) gets called once per event per wafer.
- It first loops over the trigger cells, remaps from the TC U/V coordinates to the 0-47 indexing we have been using for the training, then fills the mipPt list.
```  
for (const auto& trigCell : trigCellVecInput) {
    ...
    modSum += trigCell.mipPt();
}
```
- Then it normalizes the mipPt list, and quantizes it. 
- Puts stuff into tensors and [runs the encoder with tensorflow](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc#L198-L225)
- [Runs the decoder](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc#L227-L248)
- Loops over decoded values, and [puts them back into trigger cell objects](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc#L256-L304) (which is what the backend code is expecting and uses)
- There are different configuration options, to allow multiple trainings for different number of eLinks in the [hgcalConcentratorProducer](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/python/hgcalConcentratorProducer_cfi.py#L184-L226)

[comment]: <> (Danny's config /uscms/home/dnoonan/work/HGCAL/CMSSW_11_2_0_pre5/src/L1Trigger/L1THGCalUtilities/test/NewTrainings_QKeras_cfg.py)
[comment]: <> (it requires the models dir /uscms/home/dnoonan/work/HGCAL/CMSSW_11_2_0_pre5/src/L1Trigger/L1THGCalUtilities/test/AEmodels)

## e/g cluster energy correction and resolution study


### Preprocessing
The preprocessing script `scripts/matching.py` takes as input HGCAL TPG ntuples and produces pandas dataframes in HDF files. It is selecting gen particles reaching the HGCAL and matching them with reconstructed clusters. This step is done for electrons, photons and pions.

As it can take some time to run on all events, this script is associated with a job launcher script `scripts/submit_condor.py`, which launches jobs to run on multiple input files. 

An example of configuration file is provided in `scripts/batch_matching_autoencoder_sigdriven_210611_cfg.py`. The command is:
```bash
cd scripts/
mkdir -p condor/
python submit_condor.py --cfg batch_matching_autoencoder_sigdriven_210611_cfg
```
(Note that the config file is given without the `.py` extension)

This script will create condor submission files. 

To be able to run these files (in cmslpc) you should tar your python3 CMSSW environment and copy it to your eos.
```
cd $CMSSW_BASE/../
tar -zvcf CMSSW_11_3_0.tgz CMSSW_11_3_0  --exclude="*.pdf" --exclude="*.pyc" --exclude=tmp --exclude-vcs --exclude-caches-all --exclude="*err*" --exclude=*out_* --exclude=condor --exclude=.git --exclude=src
mv CMSSW_11_3_0.tgz /eos/uscms/store/user/$USER/
```

Then you can execute the condor submission, e.g.:
```
  condor_submit condor/3_22_1/electron_photon_signaldriven//v_1_2021-06-11/photons/submit.cmd 
  condor_submit condor/3_22_1/electron_photon_signaldriven//v_1_2021-06-11/electrons/submit.cmd 
```

(make sure you have a valid proxy before submitting condor jobs).

### Setup for python notebooks
You can execute this notebeook in your own computer (w. python3 and uproot4). You can also create a conda environment with all the needed packages:

```
conda create -n econ-ae python=3.8
conda activate econ-ae
pip install numpy pandas scikit-learn scipy matplotlib uproot coffea jupyterlab xgboost tables
```

And then, download the data you just processed, e.g.:
```
cd notebooks/
mkdir data/
mkdir img/
scp -r cmslpc-sl7.fnal.gov:/eos/uscms/store/user/cmantill/HGCAL/study_autoencoder/3_22_1/ data/
```

### Energy correction and resolution notebook
The dataframes produced at the preprocessing step are used in the notebook `notebooks/electron_photon_calibration_autoencoder_210430.ipynb`. This notebook is performing the following:
- Derive layer weight correction factors with 0PU **unconverted** photons
- Derive $\eta$ dependent linear energy correction (this is an additive correction) with 200PU electrons
- Produce energy scale and resolution plots, in particular differentially vs  $|\eta|$ and $p_T$

The output of this notebook is used for the next step so make sure you upload your data folder to the repository.

## Electron vs PU discrimination
### Preprocessing
Electron preprocessed files produced in the previous step are used here as well. Only PU events need to be preprocessed now. This is very similar to the electron and photon preprocessing, except that no matching is performed, and energy corrections previously derived are applied to PU clusters.

The PU preprocessing script is `scripts/clusters2hdf.py` and the associated configs needs to have the clustering option = 0.
An example of config file is provided in `scripts/batch_nomatching_pu_for_id_autoencoder_sigdriven_210430_cfg.py`. The command is:
```bash
python submit_condor.py --cfg batch_nomatching_pu_for_id_autoencoder_sigdriven_210430_cfg
```
(Note that the config file is given without the `.py` extension)

### BDT hyperparameters tuning notebook
It is important to note that trigger rates, which is the ultimate metric, require a lot of statistics. Given the size of the available neutrino gun or MinBias samples, the full statistics of these samples need to be used to produce final rate plots. Which means that a lot of attention should be put on the control of the overtraining of our BDTs, since they will be applied on events used to train them.

The notebook `notebooks/electron_pu_bdt_tuning_autoencoder_210430.ipynb` is meant to find the set of hyperparameters to be used later, with focus on the limitation of overtraining rather than optimal performance. This hyperparameter tuning is currently done by hand, and some automatization could be implemented.  XGBOOST is used to train the BDTs. This notebook is doing the following:
- Scan of L1 and L2 regularization parameters. 
- Scan of the learning rate. 
- Scan of the tree depth. 
- Checking the behaviour as a function of the number of boosting steps. 
- Checking overtraining with a final set of hyperparameters

### BDT final training notebook
The final BDT ID training performed on the full sample is done in the notebook `notebooks/electron_pu_autoencoder_210430.ipynb`. Signal efficiencies as a function of $\eta$ and $p_T$ are computed, for a 99% inclusive signal efficiency working point.

## Turnons and L1 $\to$ offline threshold mapping
The energy corrections and BDT ID are then used to compute the efficiency turnons in the notebook `notebooks/electron_turnon_autoencoder_210430.ipynb`. 

The turnon curves are finally used to extract the L1 $\to$ offline threshold mappings, which will be used to compare L1 rates as a function of the so-called offline threshold. In our case this offline threshold is defined as the gen-level $p_T$ at which the turnon reaches 95% efficiency.

## Rates
### Preprocessing
The PU preprocessing is rerun with different settings, adding a cluster selection based on the ID BDT, and storing only the maximum $p_T$ cluster passing the ID selection.

The config file is `scripts/batch_nomatching_pu_discri_autoencoder_sigdriven_210430_cfg.py`, and the command is, as before:
```bash
batch_nomatching.py --cfg batch_nomatching_pu_discri_autoencoder_sigdriven_210430_cfg
```
(Note that the config file is given without the `.py` extension)

### Rates notebook
Rate extraction and plotting are implemented in the notebook `notebooks/egamma_rates_autoencoder_210430.ipynb` . Rates as a function of the offline threshold are the final plots used to compare the different algorithms.
