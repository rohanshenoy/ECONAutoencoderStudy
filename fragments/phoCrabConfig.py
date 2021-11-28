from CRABClient.UserUtilities import config
config = config()

config.General.requestName = 'AE_photons_11_22_1'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'produce_ntuple_std_ae_xyseed_reduced_genmatch_v11_cfg.py'
config.JobType.maxMemoryMB = 4000

config.Data.inputDataset = '/SingleElectron_PT2to200/Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_111X_mcRun4_realistic_T15_v1_ext2-v1/FEVT'
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
config.Data.outLFNDirBase = '/store/user/rshenoy/HGCAL/AE_Nov22/'
config.Data.unitsPerJob = 10

config.Data.publication = False
config.Site.storageSite = 'T3_US_FNALLPC'

