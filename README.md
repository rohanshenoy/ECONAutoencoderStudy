Scripts and notebooks in this package should be run with python 3 (they have been tested with python 3.7). The main dependencies are:
- scipy
- numpy
- pandas
- uproot (version 4)
- scikit-learn
- xgboost

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

### Energy correction and resolution notebook
The dataframes produced at the preprocessing step are used in the notebook `notebooks/electron_photon_calibration_autoencoder_210430.ipynb`. This notebook is performing the following:
- Derive layer weight correction factors with 0PU **unconverted** photons
- Derive $\eta$ dependent linear energy correction (this is an additive correction) with 200PU electrons
- Produce energy scale and resolution plots, in particular differentially vs  $|\eta|$ and $p_T$

## Electron vs PU discrimination
### Preprocessing
Electron preprocessed files produced in the previous step are used here as well. Only PU events need to be preprocessed now. This is very similar to the electron and photon preprocessing, except that no matching is performed, and energy corrections previously derived are applied to PU clusters.

The PU preprocessing script is `scripts/clusters2hdf.py` and the associated batch launcher is `scripts/batch_nomatching.py`. An example of config file is provided in `scripts/batch_nomatching_pu_for_id_autoencoder_sigdriven_210430_cfg.py`. The command is:
```bash
batch_nomatching.py --cfg batch_nomatching_pu_for_id_autoencoder_sigdriven_210430_cfg
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
