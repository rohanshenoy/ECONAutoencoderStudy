#!/bin/bash

matching=$1
jobid=$2

echo $1
echo $2
# remove old
source /cvmfs/cms.cern.ch/cmsset_default.sh
rm *.tgz

# copy environment
xrdcp -f root://cmseos.fnal.gov//store/user/cmantill/CMSSW_11_3_0.tgz ./CMSSW_11_3_0.tgz
tar -zxvf CMSSW_11_3_0.tgz
rm *.tgz
mkdir CMSSW_11_3_0/src
cd CMSSW_*/src
scram b ProjectRename
eval `scramv1 runtime -sh`
export PYTHONPATH=PYTHONPATH:"${CMSSW_BASE}/lib/${SCRAM_ARCH}"

cd ../../
ls -l
if [ $matching == 1 ]
then
    python3 matching.py $jobid
else
    python3 clusters2hdf.py $jobid
fi

status=$?

ls -l

exit $status
