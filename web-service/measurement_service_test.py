#!/usr/bin/python
import jsonrpclib
import os
import subprocess
import measurement_service
import time
import tempfile
import traceback
import sys
import logging.config
import json

"""
Integration test for the measurement service
"""

def assertEquals(expected, actual):
    
    try:
        assert(expected == actual)
    except AssertionError, e:
        print('Assertion failed. Expected %s but got %s' % (expected, actual))
        raise e

if __name__ == '__main__':
   
    with open('logging.json', 'r') as f:
        log_config = json.loads(f.read())
    logging.config.dictConfig(log_config)
 
    auth_file = tempfile.gettempdir()+os.sep+'service_auth'
    f = open(auth_file, 'w')
    f.write('test:test\n')
    f.close()

    

    try:
        
        print('Starting service')
        subprocess.Popen(['./measurement_service.py', '8080', config_file, auth_file])
        print('Service started')
        time.sleep(10)

        server = jsonrpclib.Server('http://test:test@localhost:8080')
    
        #fetch_single_success(server)
    except:
        sys.stderr.write('Exiting from Exception\n')
        traceback.print_exc(file=sys.stderr)

    finally:
        print('Killing service')
        subprocess.Popen(['pkill', '-f', 'measurement_service.py'])
        print('Service stopped')
    
