#!/bin/bash

if [ $# -ne 2 ]; then
   echo "Usage: user@host version"
   exit 1
fi

#initialize ssh environment variables
source ~/.ssh/environment

app="measurement-service"
port=8080
host=$1
version=$2

script_dir=$(dirname $0)
cd $script_dir

remote_base="/media/HDDEX1/matt/$app"
remote_dir="$remote_base/$version"

#create remote directory structure if it doesn't exist. create symlink to CURRENT
cmd="if [ ! -d $remote_dir ]; then mkdir --parents $remote_dir; fi; rm -f $remote_base/CURRENT; ln -s $remote_dir $remote_base/CURRENT;"
ssh $host $cmd

if ssh $host test ! -e "$remote_base/logging.json" -a ! -e "$remote_base/config.yml"; then
    echo "logging and config have not been configured! Exiting."
    exit 1
fi

#perform upload
echo "uploading files to $host:$remote_dir"
scp *.py $host:$remote_dir

#restart
echo "restarting $app"
ssh $host "pkill -f $app"
ssh $host "$remote_base/run $port"
