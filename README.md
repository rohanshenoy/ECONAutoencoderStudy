Scripts and notebooks in this package should be run with python 3 (they have been tested with python 3.7). The main dependencies are:
- scipy
- numpy
- pandas
- uproot (version 4)
- scikit-learn
- xgboost

## Setup at cmslpc 
For procesing data and submitting condor jobs.

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
wget https://raw.githubusercontent.com/rohanshenoy/ECONAutoencoderStudy/master/fragments/produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py
wget https://raw.githubusercontent.com/rohanshenoy/ECONAutoencoderStudy/master/fragments/produce_ntuple_std_ae_xyseed_reduced_genmatch_v11_cfg.py
```

Get training models:
```
cd  ../L1THGCal/data/
# copy AEmodels folder in data/ dir 
#EMD models: https://www.dropbox.com/s/812m6a2vqgu5wwn/AEmodels.tar.gz?dl=0
#Quantized models: https://www.dropbox.com/s/kazwsfsejqcci3g/QAEmodels.tar.gz?dl=0
# i.e. scp AEmodels.tgz cmslpc-sl7.fnal.gov:YOURLOCATION/L1THGCal/data/ 
tar zxvf AEmodels.tgz
# then go back to your directory
cd -
```

### Running locally
Then you can run locally, e.g.:
```
cmsRun produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py
```
(`produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py` contains a file that can be found in the cmslpc cluster so there is no need to have a grid certificate for this step).
This will produce a `ntuple.root` file, which will contain subdirectories, e.g. `FloatingpointAutoEncoderTelescopeMSEDummyHistomaxxydr015Genclustersntuple->cd()` , each with a TTree inside. You can get the contents of the tree with `HGCalTriggerNtuple->Show(0)`.

### Running jobs in crab
To submit a large production you will need to run over all the files. 
You can use `crab` for this. This needs a valid GRID certificate.

The crab configuration files are in the `fragments/` folder. You can download them to the `test/` directory. See e.g. [here for electrons](https://github.com/cmantill/ECONAutoencoderStudy/blob/master/fragments/eleCrabConfig.py). Make sure to change the output username.
Then do e.g. `crab submit eleCrabConfig.py`.

Some example files are already produced here:
```
/eos/uscms/store/user/cmantill/HGCAL/AE_Jun11/
```

You can look at the contents of one file, for example:
```
/eos/uscms/store/user/cmantill/HGCAL/AE_Jun11/SinglePhoton_PT2to200/crab_AE_photons_3_23_2/210611_190930/0000/ntuple_8.root
```

### Post-processing with condor 
There are several post-processing steps that we can do to these input files:
- Generator Level Matching with reconstructed clusters: For this we use `scripts/matching.py`. It takes as input the HGCAL TPG ntuples (produced in the last step) and produces pandas dataframes in HDF files. It is selecting gen particles reaching the HGCAL and matching them with reconstructed clusters. This step is done for electrons, photons and pions.
   -  The output of the `matching` step is used in the `Energy correction and resolution notebook` (described later)
- Saving reconstructed clusters information after applying energy corections For this we use `scripts/clusters2hdf.py`. The script is very similar to the last one, except that no matching is performed, and energy corrections derived in the `notebooks/electron_photon_calibration_autoencoder_210611.ipynb` notebook, are applied to PU clusters. Therefore, this step should be done once the latter step is completed.

As it can take some time to run on all events, both scripts are associated with a job launcher script `scripts/submit_condor.py`, which launches jobs to run on multiple input files. 

To be able to run files (in cmslpc) you should tar your python3 CMSSW environment and copy it to your eos space. Also you should have a valid proxy.
```
cd $CMSSW_BASE/../
tar -zvcf CMSSW_11_3_0.tgz CMSSW_11_3_0  --exclude="*.pdf" --exclude="*.pyc" --exclude=tmp --exclude-vcs --exclude-caches-all --exclude="*err*" --exclude=*out_* --exclude=condor --exclude=.git --exclude=src
mv CMSSW_11_3_0.tgz /eos/uscms/store/user/$USER/
```

An example of configuration file is provided in `scripts/batch_matching_autoencoder_sigdriven_210611_cfg.py`. The command is:
```bash
cd scripts/
mkdir -p condor/
python submit_condor.py --cfg batch_matching_autoencoder_sigdriven_210611_cfg # (e/g cluster energy correction and resolution study)
```
(Note that the config file is given without the `.py` extension)

This script will create condor submission files. 

Then you can execute the condor submission, e.g.:
```
  condor_submit condor/3_22_1/electron_photon_signaldriven/v_1_2021-06-11/photons/submit.cmd 
  condor_submit condor/3_22_1/electron_photon_signaldriven/v_1_2021-06-11/electrons/submit.cmd 
```

(make sure you have a valid proxy before submitting condor jobs).

Otherwise, you can find example dataframes already produced here:

```
/eos/uscms/store/user/cmantill/HGCAL/study_autoencoder/3_22_1/electron_photon_signaldriven/*
e.g.
/eos/uscms/store/user/cmantill/HGCAL/study_autoencoder/3_22_1/electron_photon_signaldriven/v_1_2021-06-11/electrons/electrons_0.hdf5
```

The same step needs to be repeated to processed pileup (PU) events. 
The PU preprocessing script is `scripts/clusters2hdf.py` and the associated configs needs to have the `clustering option = 0`.

An example of config file is provided in `scripts/batch_nomatching_pu_for_id_autoencoder_sigdriven_210611_cfg.py`. The command is:
```bash
python3 submit_condor.py --cfg batch_nomatching_pu_for_id_autoencoder_sigdriven_210611_cfg
```
(Note that the config file is given without the `.py` extension and that we need python3 to open the pickle files)

The dataframes produced in this step can be used to train a discriminator (BDT) that classifies signal (electrons) and background (pileup). 

The PU preprocessing can then be rerun with different settings, adding a cluster selection based on the ID BDT, and storing only the maximum $p_T$ cluster passing the ID selection.

The config file is `scripts/batch_nomatching_pu_discri_autoencoder_sigdriven_210611_cfg.py`, and the command is, as before:
```bash
python3 submit_condor.py --cfg batch_nomatching_pu_discri_autoencoder_sigdriven_210611_cfg
```
(Note that the config file is given without the `.py` extension and that we need python3 to open the pickle files)

## Setup for juptyer notebooks
For running the notebooks that analyze the pandas dataframes.

If you are able, you can create a conda environment locally:
```
conda create -n econ-ae python=3.7 # note that 3.7 is important to have dataframe compatibility (otherwise run dataframes w. python 3.8)
conda activate econ-ae
pip install numpy pandas scikit-learn scipy matplotlib uproot coffea jupyterlab tables
pip install "xgboost==1.3.3"
```

or you can use JupyterHub. For this, point your browser to:
https://jupyter.accre.vanderbilt.edu/

Click the "Sign in with Jupyter ACCRE" button. On the following page, select CERN as your identity provider and click the "Log On" button. Then, enter your CERN credentials or use your CERN grid certificate to authenticate. Select a "Default ACCRE Image v5" image and then select either 1 core/2 GB or memory or 8 cores/8GB memory. Unless you are unable to spawn a server, we recommend using the 8 core/8GB memory servers as notebooks 4 and 5 require a lot of memory. Once you have selected the appropriate options, click "Spawn".

Now you should see the JupyterHub home directory. Click on "New" then "Terminal" in the top right to launch a new terminal.

Once any of these steps are done (conda or jupyter in vanderbilt) then you can clone the repository:
```
git clone git@github.com:cmantill/ECONAutoencoderStudy.git
```

And then, download the input data (processed with the configuration files in `fragments`), e.g.:
```
cd notebooks/
mkdir data/
mkdir img/
scp -r cmslpc-sl7.fnal.gov:/eos/uscms/store/user/cmantill/HGCAL/study_autoencoder/3_22_1/ data/
```

For the 2nd and so on notebooks you will need python 3.8, as well as scikit-learn (0.24.1 ?).

## Description of input data for physics studies

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

## Notebooks:

- `electron_photon_calibration_autoencoder_210611.ipynb`:
   - Derives layer weight correction factors with 0PU unconverted photons
   - Derives $\eta$ dependent linear energy correction (this is an additive correction) with 200PU electrons
   - Produces energy scale and resolution plots, in particular differentially vs $|\eta|$ and $p_T$
- `electron_pu_bdt_tuning_autoencoder_210611.ipynb`: 
   - Finds the set of hyperparameters to be used later in the training of BDT (discriminator between electrons and PileUp). XGBOOST is used to train the BDTs.
      - Scans the L1 and L2 regularization parameters. 
      - Scans the learning rate. 
      - Scans the BDT tree depth. 
   - Checks the behaviour of the BDT as a function of the number of boosting steps. 
   - Checks for overtraining with a final set of hyperparameters. The notebook focuses on the limitation of overtraining rather than optimal performance. This hyperparameter tuning is currently done by hand, and some automatization could be implemented. 
- `electron_pu_autoencoder_210611.ipynb`: 
   - Performs the final BDT ID training on the full sample
   - Computes the signal efficiencies as a function of $\eta$ and $p_T$, for a 99% inclusive signal efficiency working point.
- `electron_turnon_autoencoder_210611.ipynb`: 
   - Computes the trigger efficiency turn on curves (using the energy corrections and the BDT ID)
   - The turn-on curves are finally used to extract the L1 $\to$ offline threshold mappings, which will be used to compare L1 rates as a function of the so-called offline threshold. In our case this offline threshold is defined as the gen-level $p_T$ at which the turnon reaches 95% efficiency.
- `egamma_rates_autoencoder_210611.ipynb`: 
   - Extracts the rate and plots the rate as a function of the offline threshold.
   - These are the final plots used to compare the different algorithms.
