#!/bin/bash

base_dir=/data/work/crypto-alert
cd $base_dir

jobDir=`pwd`
pythonPath=${base_dir}/venv/bin/python

logName=funding_rate_monitor
jobName=funding_rate_monitor.py

. colors.sh

TAILPID=`ps aux | grep "$jobName" | grep -v grep | awk '{print $2}'`
echo "${YELLOW}check $jobName pid $TAILPID ${NOCOLOR}"
[ "0$TAILPID" != "0" ] && kill -9 $TAILPID

mkdir -p logs


echo "${YELLOW}nohup $pythonPath $jobDir/$jobName > logs/${logName}.log 2>&1 &${NOCOLOR}"
nohup $pythonPath $jobDir/$jobName > logs/${logName}.log 2>&1 &
