#!/usr/bin/env python

import numpy as np
import pandas as pd
import os
import sys
import uproot4
from datetime import date
import argparse
from itertools import chain
import xgboost as xgb
import subprocess

from sklearn.linear_model import LinearRegression

workdir=os.getcwd()

def slice_it(li, cols=2):
    start = 0
    for i in range(cols):
        stop = start + len(li[i::cols])
        yield li[start:stop]
        start = stop

def maxpt(group):    
    maxi = group.loc[group['cl3d_pt_corr'].idxmax()]
    return maxi

def xrd_prefix(filepaths):
    prefix = ''
    allow_prefetch = False
    if not isinstance(filepaths, (list, tuple)):
        filepaths = [filepaths]
    filepath = filepaths[0]
    if filepath.startswith('/eos/cms'):
        prefix = 'root://eoscms.cern.ch/'
    elif filepath.startswith('/eos/user'):
        prefix = 'root://eosuser.cern.ch/'
    elif filepath.startswith('/eos/uscms'):
        prefix = 'root://cmseos.fnal.gov/'
    elif fillepath.startswith('/store/'):
        # remote file                                                                                                                                                                                                                                                         
        import socket
        host = socket.getfqdn()
        if 'cern.ch' in host:
            prefix = 'root://xrootd-cms.infn.it//'
        else:
            prefix = 'root://cmseos.fnal.gov//'
        allow_prefetch = True
    expanded_paths = [(prefix + '/' + f if prefix else f) for f in filepaths]
    return expanded_paths, allow_prefetch

def get_entries(filename,algo_tree):
    import ROOT
    rootfile = ROOT.TFile.Open(filename)
    nentries = rootfile.Get(algo_tree).GetEntries()
    rootfile.Close()
    print(nentries)
    return nentries

def openroot(files, algo_trees, bdts, working_points,
        calibration_weights, correction_cluster, correction_inputs, additive_correction,
        ptcut, store_max_only):
    gens = []
    algos = {}
    events = 0
    branches_cl3d=['event','cl3d_pt','cl3d_eta','cl3d_phi','cl3d_showerlength',
            'cl3d_coreshowerlength','cl3d_firstlayer','cl3d_maxlayer','cl3d_seetot',
            'cl3d_spptot','cl3d_szz', 'cl3d_srrtot', 'cl3d_srrmean',
            'cl3d_hoe', 'cl3d_meanz', 'cl3d_layer10', 'cl3d_layer50',
            'cl3d_layer90', 'cl3d_ntc67', 'cl3d_ntc90']
    
    for filename in files:
        '''
        print('> Copying', filename)
        cwd = os.getcwd()
        tmpname = cwd+'/'+filename.split('/')[-1]
        cmd = 'xrdcp --silent -p -f {inputname} {tmpname}'.format(
            inputname=filename, tmpname=tmpname)
        print(cmd)
        p = subprocess.Popen(cmd, shell=True)
        print('> Reading', tmpname)
        print(os.listdir())
        print(os.path.isfile(tmpname))
        '''
    
        ialgo = 0
        entry_stop = 3000
        for algo_name, algo_tree in algo_trees.items():
            print('>>', algo_name)
            if not algo_name in algos:
                algos[algo_name] = []

            nentries = get_entries(filename,algo_tree)

            entries_to_split = slice_it(range(0,nentries),10)
            for ie,to_split in enumerate(entries_to_split):
                print('to split ',to_split)

            uproot4.open.defaults["xrootd_handler"] = uproot4.source.xrootd.MultithreadedXRootDSource
            tree = uproot4.open(filename)[algo_tree]
            df_cl = tree.arrays(branches_cl3d, library='pd', entry_stop=entry_stop)
            # Counting number of events before any preselection
            if ialgo==0:
                events += np.unique(df_cl['event']).shape[0]
            ialgo += 1
            # Trick to read layers pTs, which is a vector of vector
            df_cl['cl3d_layer_pt'] = list(chain.from_iterable(tree.arrays(['cl3d_layer_pt'], entry_stop=entry_stop)[b'cl3d_layer_pt'].tolist()))
            df_cl['cl3d_abseta'] = np.abs(df_cl.cl3d_eta)
            # Applying layer weights and cluster correction
            if calibration_weights and correction_cluster:
                print('>>> Applying layer weights')
                layers = np.array(df_cl['cl3d_layer_pt'].tolist())[:,2:15]
                df_cl['cl3d_pt_calib'] = np.dot(layers, calibration_weights[algo_name])
                print('>>> Applying energy correction')
                df_cl['cl3d_corr'] = correction_cluster[algo_name].predict(df_cl[correction_inputs])
                if additive_correction:
                    df_cl['cl3d_pt_corr'] = df_cl.cl3d_corr + df_cl.cl3d_pt_calib
                else:
                    df_cl['cl3d_pt_corr'] = df_cl.cl3d_corr*df_cl.cl3d_pt_calib
            else:
                df_cl['cl3d_pt_calib'] = df_cl.cl3d_pt
                df_cl['cl3d_pt_corr'] = df_cl.cl3d_pt
            print('>>> Total number of cluster', df_cl.shape[0])
            print('Applying cut on corrected pT')
            df_cl = df_cl[df_cl.cl3d_pt_corr > ptcut]
            print('>>> Number of clusters after pT cut', df_cl.shape[0])
            # Applying ID cut
            if working_points[algo_name] > -999.:
                print('>>> Computing BDT output')
                feature_names = bdts[algo_name].feature_names
                matrix = xgb.DMatrix(data=df_cl[feature_names], feature_names=feature_names)
                df_cl['cl3d_xgb'] = bdts[algo_name].predict(matrix)
                print('>>> Applying BDT cut')
                df_cl = df_cl[df_cl.cl3d_xgb > working_points[algo_name]]
            print('>>> Number of clusters after ID', df_cl.shape[0])
            if store_max_only:
                print('>> Selecting max pt cluster only')
                df_cl = df_cl.groupby('event').apply(maxpt)
            print('>>> Number of final clusters', df_cl.shape[0])

            algos[algo_name].append(df_cl)

    df_algos = {}
    for algo_name, dfs in algos.items():
        df_algos[algo_name] = pd.concat(dfs)
        df_algos[algo_name].set_index('event', inplace=True)
    return events, df_algos

def get_output_name(md, jobid):
    info = md['jobs'][jobid]
    return '{samp}_{idx}.hdf5'.format(samp=md['name'], idx=info['idx'])

def preprocessing(md):
    files= md['jobs'][args.jobid]['inputfiles']
    algo_trees=md['algo_trees']

    output_name = get_output_name(md, args.jobid)

    bdts = md['bdts']
    working_points = md['working_points']
    correction_cluster = md['correction_cluster']
    correction_inputs = md['correction_inputs']
    calibration_weights = md['calibration_weights']
    store_max_only = md['store_max_only']
    additive_correction = md['additive_correction']
    ptcut = md['pt_cut']

    events, algo = openroot(files, algo_trees, bdts, working_points, 
                            calibration_weights, correction_cluster, correction_inputs, additive_correction,
                            ptcut, store_max_only)
    
    #save files to savedir in HDF
    store = pd.HDFStore(output_name, mode='w')
    for algo_name, df in algo.items():
        store[algo_name] = df
    store.close()

    # Save number of events before preselection
    with open(os.path.splitext(output_name)[0]+'.txt', 'w') as f:
        print(events, file=f)

    cmd = 'xrdcp --silent -p -f {outputname} {outputdir}/{outputname} \n'.format(
        outputname=output_name, outputdir=xrd_prefix(md['joboutputdir'])[0][0])
    cmd += 'xrdcp --silent -p -f {outputname} {outputdir}/{outputname}'.format(
        outputname=os.path.splitext(output_name)[0]+'.txt', outputdir=xrd_prefix(md['joboutputdir'])[0][0])
    print(cmd)
    p = subprocess.Popen(cmd, shell=True)        
        
if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--metadata',default='metadata.json',
                        help='Path to the metadata file. Default:%(default)s')
    parser.add_argument('jobid', type=int, help='Index of the output job.')

    args = parser.parse_args()

    # Loading configuration parameters
    if '.json' in args.metadata:
        import json
        with open(args.metadata) as fp:
            md = json.load(fp)
    else:
        import pickle
        with open(args.metadata, 'rb') as fp:
            md = pickle.load(fp)
        print(md)

    preprocessing(md)

