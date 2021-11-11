import FWCore.ParameterSet.Config as cms 

from Configuration.Eras.Era_Phase2C9_cff import Phase2C9
process = cms.Process('DIGI',Phase2C9)

# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.Geometry.GeometryExtended2026D49Reco_cff')
process.load('Configuration.Geometry.GeometryExtended2026D49_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.Generator_cff')
process.load('IOMC.EventVertexGenerators.VtxSmearedHLLHC14TeV_cfi')
process.load('GeneratorInterface.Core.genFilterSummary_cff')
process.load('Configuration.StandardSequences.SimIdeal_cff')
process.load('Configuration.StandardSequences.Digi_cff')
process.load('Configuration.StandardSequences.SimL1Emulator_cff')
process.load('Configuration.StandardSequences.DigiToRaw_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')


process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(5)
)

# Input source
process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring('/store/mc/Phase2HLTTDRWinter20DIGI/SingleElectron_PT2to200/GEN-SIM-DIGI-RAW/PU200_110X_mcRun4_realistic_v3_ext2-v2/40000/00582F93-5A2A-5847-8162-D81EE503500F.root'),
                            #fileNames = cms.untracked.vstring('file:/data_cms_upgrade/sauvan/HGCAL/DIGI/Phase2HLTTDRWinter20DIGI/TT_TuneCP5_14TeV-powheg-pythia8/GEN-SIM-DIGI-RAW/PU200_110X_mcRun4_realistic_v3-v2/2D0339A5-751F-3543-BA5B-456EA6E5E294.root'),
       inputCommands=cms.untracked.vstring(
           'keep *',
           'drop l1tEMTFHit2016Extras_simEmtfDigis_CSC_HLT',
           'drop l1tEMTFHit2016Extras_simEmtfDigis_RPC_HLT',
           'drop l1tEMTFHit2016s_simEmtfDigis__HLT',
           'drop l1tEMTFTrack2016Extras_simEmtfDigis__HLT',
           'drop l1tEMTFTrack2016s_simEmtfDigis__HLT',
           )
       )

process.options = cms.untracked.PSet(

)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    version = cms.untracked.string('$Revision: 1.20 $'),
    annotation = cms.untracked.string('SingleElectronPt10_cfi nevts:10'),
    name = cms.untracked.string('Applications')
)

# Output definition
process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string("ntuple.root")
    )

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic', '')

# load HGCAL TPG simulation
process.load('L1Trigger.L1THGCal.hgcalTriggerPrimitives_cff')
process.load('L1Trigger.L1THGCalUtilities.HGC3DClusterGenMatchSelector_cff')
process.load('L1Trigger.L1THGCalUtilities.hgcalTriggerNtuples_cff')
from L1Trigger.L1THGCalUtilities.hgcalTriggerChains import HGCalTriggerChains
import L1Trigger.L1THGCalUtilities.vfe as vfe
import L1Trigger.L1THGCalUtilities.concentrator as concentrator
import L1Trigger.L1THGCalUtilities.clustering2d as clustering2d
import L1Trigger.L1THGCalUtilities.clustering3d as clustering3d
import L1Trigger.L1THGCalUtilities.selectors as selectors
import L1Trigger.L1THGCalUtilities.customNtuples as ntuple

# Change cluster threshold
process.histoMax_C3d_clustering_params.minPt_multicluster = 5.
# fill cluster layer info
process.ntuple_multiclusters.FillLayerInfo = True


chains = HGCalTriggerChains()
# Register algorithms
## VFE
chains.register_vfe("Floatingpoint", vfe.create_vfe)
## ECON
chains.register_concentrator("Threshold",
        concentrator.create_threshold)
chains.register_concentrator('Threshold0',
        lambda p,i :concentrator.create_threshold(p,i,
            threshold_silicon=0.,threshold_scintillator=0.))
chains.register_concentrator("Mixedbcstc", 
                             concentrator.create_mixedfeoptions)

# AE models
triggerCellRemap = [28,29,30,31,0,4,8,12,
                    24,25,26,27,1,5,9,13,
                    20,21,22,23,2,6,10,14,
                    16,17,18,19,3,7,11,15,
                    47,43,39,35,-1,-1,-1,-1,
                    46,42,38,34,-1,-1,-1,-1,
                    45,41,37,33,-1,-1,-1,-1,
                    44,40,36,32,-1,-1,-1,-1]

AE_8x8_pool_telescope = cms.PSet(encoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_tele/encoder.pb'),
                                 decoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_tele/decoder.pb'))
chains.register_concentrator("AutoEncoderTelescopeMSE", 
                             lambda p, i : concentrator.create_autoencoder(p, i, 
                                                                           modelFiles = cms.VPSet([AE_8x8_pool_telescope]), 
                                                                           linkToGraphMap = cms.vuint32([0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
                                                                           encoderShape=cms.vuint32([1,8,8,1]),
                                                                           cellRemap = cms.vint32(triggerCellRemap),
                                                                           cellRemapNoDuplicates = cms.vint32(triggerCellRemap)))

AE_8x8_c8_S2_ae_mse = cms.PSet(encoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_ae_mse/encoder.pb'),
                                 decoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_ae_mse/decoder.pb'))
chains.register_concentrator("AutoEncoderEMDAEMSE", 
                             lambda p, i : concentrator.create_autoencoder(p, i, 
                                                                           modelFiles = cms.VPSet([AE_8x8_c8_S2_ae_mse]), 
                                                                           linkToGraphMap = cms.vuint32([0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
                                                                           encoderShape=cms.vuint32([1,8,8,1]),
                                                                           cellRemap = cms.vint32(triggerCellRemap),
                                                                           cellRemapNoDuplicates = cms.vint32(triggerCellRemap)))

AE_8x8_c8_S2_pair_huber= cms.PSet(encoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_pair_huber/encoder.pb'),
                                   decoderModelFile = cms.FileInPath('L1Trigger/L1THGCal/data/QAEmodels/8x8_c8_S2_pair_huber/decoder.pb'))
chains.register_concentrator("AutoEncoderEMDPAIRMSE", 
                             lambda p, i : concentrator.create_autoencoder(p, i, 
                                                                           modelFiles = cms.VPSet([AE_8x8_c8_S2_pair_huber]), 
                                                                           linkToGraphMap = cms.vuint32([0,0,0,0,0,0,0,0,0,0,0,0,0,0]),
                                                                           encoderShape=cms.vuint32([1,8,8,1]),
                                                                           cellRemap = cms.vint32(triggerCellRemap),
                                                                           cellRemapNoDuplicates = cms.vint32(triggerCellRemap)))

## BE1
chains.register_backend1("Dummy", clustering2d.create_dummy)
## BE2
from L1Trigger.L1THGCal.hgcalBackEndLayer2Producer_cfi import MAX_LAYERS
dr015 = [0.015]*(MAX_LAYERS+1)
chains.register_backend2("Histomaxxydr015",
        lambda p,i : clustering3d.create_histoMaxXY_variableDr(p,i,
        distances=dr015))
# Register ntuples
ntuple_list = ['event', 'gen', 'multiclusters']
chains.register_ntuple("Genclustersntuple", lambda p,i : ntuple.create_ntuple(p,i, ntuple_list))

# Register trigger chains
concentrator_algos = [
        'Threshold','Threshold0','Mixedbcstc',
        'AutoEncoderTelescopeMSE','AutoEncoderEMDAEMSE','AutoEncoderEMDPAIRHUBER'
        ]
backend_algos = ['Histomaxxydr015']
## Make cross product fo ECON and BE algos
import itertools
for cc,be in itertools.product(concentrator_algos,backend_algos):
    chains.register_chain('Floatingpoint', cc, 'Dummy', be, '', 'Genclustersntuple')

process = chains.create_sequences(process)

# Remove towers from sequence
process.hgcalTriggerPrimitives.remove(process.hgcalTowerMap)
process.hgcalTriggerPrimitives.remove(process.hgcalTower)

process.hgcl1tpg_step = cms.Path(process.hgcalTriggerPrimitives)
process.selector_step = cms.Path(process.hgcalTriggerSelector)
process.ntuple_step = cms.Path(process.hgcalTriggerNtuples)

# Schedule definition
process.schedule = cms.Schedule(process.hgcl1tpg_step, process.selector_step, process.ntuple_step)

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion

