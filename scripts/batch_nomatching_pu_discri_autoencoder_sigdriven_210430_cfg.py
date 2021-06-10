from glob import glob
import pickle
import numpy as np

# Flag to test locally
local = False


files_batch = glob('/home/llr/cms/sauvan/DATA_UPG/HGCAL/Ntuples/study_autoencoder/3_22_1/MinBias_TuneCP5_14TeV-pythia8/MinBias_PU200_HLTWinter20_std_ae_sigdriven_xyseed/210430_091906/ntuple*.root')
# if local test, use only one input file
if local:
    files_batch = files_batch[:1]
output_dir = '/home/llr/cms/sauvan/DATA_UPG/HGCAL/Dataframes/study_autoencoder/3_22_1/pu_discri_signaldriven/'
file_per_batch = 5


# List of ECON algorithms
fes = ['Threshold0', 'Threshold', 'Mixedbcstc',
        'AutoEncoderTelescopeMSE', 'AutoEncoderStride',
        'AutoEncoderQKerasTTbar', 'AutoEncoderQKerasEle',
        ]

ntuple_template = 'Floatingpoint{fe}Dummy{be}Genclustersntuple/HGCalTriggerNtuple'
algo_trees = {}
for fe in fes:
    be = 'Histomaxxydr015'
    algo_trees[fe] = ntuple_template.format(fe=fe, be=be)

# Clusters with a corrected pT below 0GeV are cut
# Note: there's a 5GeV pT cut applied at the ntuple level on the uncorrected pT
pt_cut = 0
# Store only the maximum pT cluster (corrected pT)
# Note: it is the maximum pT cluster among the clusters passing the ID
store_max_only = True

# Load energy calibration/correction data
with open('/home/llr/cms/sauvan/Projects/L1CalorimeterTrigger_Phase2HGCal/Studies/HGCTPGBackendStudies/data/layer_weights_photons_autoencoder_210430.pkl', 'rb') as f:
    calibration_weights = pickle.load(f)
with open('/home/llr/cms/sauvan/Projects/L1CalorimeterTrigger_Phase2HGCal/Studies/HGCTPGBackendStudies/data/lineareta_electrons_autoencoder_210430.pkl', 'rb') as f:
    correction_cluster = pickle.load(f)

additive_correction = True
correction_inputs = ['cl3d_abseta']

# Load identification data
with open('/home/llr/cms/sauvan/Projects/L1CalorimeterTrigger_Phase2HGCal/Studies/HGCTPGBackendStudies/data/xgboost_electron_pu_autoencoder_210430.pkl', 'rb') as f:
    boosters = pickle.load(f)
bdts = boosters['extended']

# Apply ID selection
# 99% signal efficiency working point
with open('/home/llr/cms/sauvan/Projects/L1CalorimeterTrigger_Phase2HGCal/Studies/HGCTPGBackendStudies/data/xgboost_threshold_electron_pu_autoencoder_210430.pkl', 'rb') as f:
    thresholds = pickle.load(f)
with open('/home/llr/cms/sauvan/Projects/L1CalorimeterTrigger_Phase2HGCal/Studies/HGCTPGBackendStudies/data/xgboost_tpr_electron_pu_autoencoder_210430.pkl', 'rb') as f:
    tprs = pickle.load(f)
wp = 0.99
working_points = {}
for name in algo_trees.keys():
    working_points[name] = np.interp(wp, tprs['extended'][name], thresholds['extended'][name])
