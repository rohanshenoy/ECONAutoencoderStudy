# HGCAL TPG ntuplizer

Full documentation can be found [here](https://twiki.cern.ch/twiki/bin/viewauth/CMS/HGCALTriggerPrimitivesSimulation).
This ntuplizer is used to simulate all the ECON-T algorithms in the CMS official simulation (cmssw).

## Training data

For the purpose of training data we run it with no threshold applied (Threshold Sum algorithm) so that it saves all of the trigger cells (TCs).

The TPG training ntuples can be found in the cmslpc cluster:
- v0: `/eos/uscms/store/user/lpchgcal/ConcentratorNtuples/L1THGCal_Ntuples/TrainingSamples_Sept2020/`

These are taken as input for the ECON-T python simulation [ECONT_Emulator](https://github.com/cmantill/ECONT_Emulator/).

- The `getDataFromMC.py` script reads in the ntuples, and produces a .csv file formatted to look as the input data that goes to the ECON-T input eLinks.
This script also computes the total simEnergy alongside the simEnergy sum of each module.
- Then, `ECONT_Emulator.py` simulates the behavior of the ECON-T. For the purposes of training data it simulates the channel re-arrangement (through the multiplexer MUX) and the calibration that converts from charge to transverse-charge.
The calibrated charges are saved in a `CALQ.csv` file, which is taken as the input to the AutoEncoder training.

Output data from these intermediate steps can be found here:
- v3: `/eos/uscms/store/user/lpchgcal/ECON_Verification_Data/${sample}Data_v11Geom_layer_${layer}_job${job}.tgz`

Each of these tar files contain subdirectories for each wafer within that layer.
These contain all the actual data needed, but are split up based on wafer, not number of eLinks.

The last step is to group the outputs based on the link allocations and the number of output eLinks from the ECON-T to the backend - this is the bottleneck of how much data can be transmitted by the algorithms.
This step can be found [in this folder](https://github.com/dnoonan08/ECONT_Emulator/tree/master/MakeTrainingDataSets).

- `getTrainingData.sh`/`submitTrainingData.jdl`: run the ECONT emulator
- `splitByLinks.sh`/`submitByLink.jdl`: split the output of the emulator step into csv files based on link allocation
- `runSkim.sh`/`submitSkim.jdl` : skims out partials and modules with 0 sim energy

[comment]: <> (The `SimEnergyPatch` folder contains scripts to include information on the SimEnergy:)
[comment]: <> (- `fixSimEnergyValues.sh` is the main script which calls the others)
[comment]: <> (- `findEventTotal.py` loops through all the SimEnergy csv’s to find total sim energy in each event)
[comment]: <> (- `mergeSimEnergy.py` updates the `CALQ.csv` file for all the wafers with the total sim energy, and simEnergy as a float rather than int)


##### Number of elinks
The number of eLinks sent will vary. A single eLink, running at 1.28 Gbps, can send 32 bits of data per BX, so with:
- 2 eLinks, i.e. 64 bits per BX: we can send 3 bits for each of the 16 encoded layer values (48 total, + leaving room for a 4 bit header and 9 bit sum of the charge in the module - this is the format of the auto-encoder output)
- 3 eLinks, i.e. 96 bits per Bx: we can send 5 bits per encoded value
- 4 eLinks: 7 bits per encoded value
- 5+ eLinks: we send the full 9 bit precision of the encoded values

##### Allocation schemes
The two allocation schemes are:
- PU allocation: assigns output eLinks in a way that areas of the detector with the highest occupancy (which are typically due to PileUp) get the most eLinks.
The distribution of eLinks is roughly a function of the eta angle (since Pileup peaks at high eta).
For this, we just have a [lookup of the links assigned to each module in a csv file](https://github.com/dnoonan08/ECONT_Emulator/blob/master/Utils/ModuleLinkSummary.csv)
Here, `Layer`, `ModU`, `ModV` will uniquely identify a 8 inch wafer (or ECON, since there is one ECON-T per wafer), and ECONT_eTX is the number of links assigned to that ECON-T.

- Signal allocation: assigns more output eLinks to the	modules in layers of the detector that are closest to the shower max.
This means that the [links are assigned by layer](https://github.com/dnoonan08/ECONT_Emulator/blob/master/Utils/linkAllocation.py).
With the shower max (layer 9) being assigned 5 eLinks, the neighboring odd numbered layers (only odd layers are readout for the trigger in EE) get 4 links, then 3, then the rest get 2.
This is found for the shower max of an electron, but would be used no matter what the sample is (so e.g. using a ttbar vs electron sample will not matter here).

Our default training was trained on Signal Allocation, ttbar sample, PU 200, nElinks 5 (e.g. layer 9).

### Output data to use.
This output of the ECONT simulation code will be similar to the `CALQ.csv` file, but with a couple extra columns for book-keeping purposes.
Each row in the file represents a module but several rows can correspond to one MC event or "entry" column.

The output (and training) data from this last step (from the ECON-T simulation), can be found here:
- ttbar: (neLinks 2-5 and no sim-Energy infomation) https://cernbox.cern.ch/index.php/s/YpAWu24aw6EaBk7
- electron samples: (neLinks 2-5 with sim-Energy information) `/eos/uscms/store/user/dnoonan/AE_TrainingData/NewData/Skim/ele200PUData_TrainingData_SignalAllocation/`

## Validation data for physics studies

Running with TPG release:
- v3.22.1. (had bug on normalization fixed by danny [here](https://github.com/PFCal-dev/cmssw/commit/65625ee12e0c1a527820d20aeaaa656cf6f4df48#diff-0003f7b8caf7041ba5afce04bcfa74b1a2593d991fc3b5b84294d5ee9e680ae4)
- v3.23.3_1130 (fixes in for AE)

The implementation of AE in CMSSW is in [HGCalConcentratorAutoEncoderImpl.cc](https://github.com/PFCal-dev/cmssw/blob/v3.23.3_1130/L1Trigger/L1THGCal/src/concentrator/HGCalConcentratorAutoEncoderImpl.cc):
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

Configuration files:
- For 200PU electron gun ( /SingleElectron_PT2to200/Phase2HLTTDRWinter20DIGI-PU200_110X_mcRun4_realistic_v3_ext2-v2/GEN-SIM-DIGI-RAW) and 0PU photon gun (/SinglePhoton_PT2to200/Phase2HLTTDRWinter20DIGI-NoPU_110X_mcRun4_realistic_v3-v2/GEN-SIM-DIGI-RAW):
`produce_ntuple_std_ae_xyseed_reduced_genmatch_v11_cfg.py`

- For 200PU MinBias (/MinBias_TuneCP5_14TeV-pythia8/Phase2HLTTDRWinter20DIGI-PU200_110X_mcRun4_realistic_v3-v3/GEN-SIM-DIGI-RAW/):
`produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py`

## CMSSWW instructions

Follow the twiki, e.g.:
```
export SCRAM_ARCH=slc7_amd64_gcc900 
cmsrel CMSSW_11_3_0
cd CMSSW_11_3_0/src/
cmsenv
git cms-init
git remote add pfcaldev https://github.com/PFCal-dev/cmssw.git
git fetch pfcaldev
git cms-merge-topic -u PFCal-dev:v3.23.3_1130
scram b -j4
```

Getting configs:
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

Then you can run, e.g.:
```
cmsRun produce_ntuple_std_ae_xyseed_reduced_pt5_v11_cfg.py
```
This will produce a `ntuple.root` file, which will contain subdirectories, e.g. `FloatingpointAutoEncoderTelescopeMSEDummyHistomaxxydr015Genclustersntuple->cd()` , each with a TTree inside. You can get the contents of the tree with `HGCalTriggerNtuple->Show(0)`.

To submit a large production you will need to run over all the files. 
You can use `crab` for this.

The crab configs are e.g. [here for electrons](https://github.com/cmantill/ECONAutoencoderStudy/blob/master/fragments/eleCrabConfig.py). Make sure to change the output username.

Some example files are already produced here:
```
/eos/uscms/store/user/cmantill/HGCAL/AE_Jun11/
```

## Processing the ntuples

Refer to instructions in https://github.com/cmantill/ECONAutoencoderStudy#readme
