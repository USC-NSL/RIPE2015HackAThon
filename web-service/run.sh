#!/bin/bash

if [ $# -ne 1 ]; then
   echo "Usage: port"
   exit 1
fi

port=$1
BASE="$(cd "$(dirname "$0")" && pwd)"
LOG_CFG=$BASE/logging.json

pkill -f measurement_service
nohup $BASE/CURRENT/measurement_service.py $port $BASE/config.yml $BASE/auth_file &> $BASE/log < /dev/null &
