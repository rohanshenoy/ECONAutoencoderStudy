from glob import glob
import itertools

# Flag to test locally
local = False

# clustering
clustering_script = 'matching.py'
clustering_option = 1 # 1 for matching

# DeltaR matching threshold
threshold = 0.05

# Input files
files = {
    'photons': glob('/eos/uscms/store/user/rshenoy/HGCAL/AE_Nov22/SinglePhoton_PT2to200/crab_AE_photons_11_28_1/211128_232558/0000/*.root'),    
    'electrons': glob('/eos/uscms/store/user/rshenoy/HGCAL/AE_Nov22/SingleElectron_PT2to200/crab_AE_electrons_11_22_21/211123_220056/0000/*.root'),
    'pions': [],
}
if local:
    files['photons'] = files['photons'][:1] if len(files['photons'])>0 else []
    files['electrons'] = files['electrons'][:1] if len(files['electrons'])>0 else []
    files['pions'] = files['pions'][:1] if len(files['pions'])>0 else []

# Pick one of the different algos trees to retrieve the gen information
gen_tree = 'FloatingpointThreshold0DummyHistomaxxydr015GenmatchGenclustersntuple/HGCalTriggerNtuple'

# STore only information on the best match
bestmatch_only = True

# Output directories
eos_output_dir = '/eos/uscms/store/user/rshenoy/HGCAL/study_autoencoder/'
job_output_dir = '11_22_1/electron_photon_signaldriven/'

file_per_batch = {
    'electrons': 5,
    'pions': 2,
    'photons': 2,
}

algo_trees = {}
# List of ECON algorithms
fes = ['Threshold','Threshold0','Mixedbcstc','AutoEncoderTelescopeMSE','AutoEncoderEMDAEMSE','AutoEncoderEMDPAIRHUBER']

ntuple_template = 'Floatingpoint{fe}Dummy{be}GenmatchGenclustersntuple/HGCalTriggerNtuple'
algo_trees = {}
for fe in fes:
    be = 'Histomaxxydr015'
    algo_trees[fe] = ntuple_template.format(fe=fe, be=be)
