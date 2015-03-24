#!/usr/bin/python
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer, SimpleJSONRPCRequestHandler
from SocketServer import ForkingMixIn
from threading import Timer
import socket
from atlas import atlas_traceroute, atlas_status, fetch_active
import urllib
import datetime
import tempfile
import os
import sys
import threading
import glob
import json
import itertools
import base64
import logging
import logging.config
import requests
import time
import traceback

class SimpleForkingJSONRPCServer(ForkingMixIn, SimpleJSONRPCServer):
    
    def __init__(self, addr, requestHandler=SimpleJSONRPCRequestHandler,
                 logRequests=True, encoding=None, bind_and_activate=True,
                 address_family=socket.AF_INET, auth_map=None):

        self.auth_map = auth_map
        SimpleJSONRPCServer.__init__(self, addr, requestHandler, logRequests,
                                     encoding, bind_and_activate, address_family)

class SecuredHandler(SimpleJSONRPCRequestHandler):

    def __init__(self, request, client_address, server, client_digest=None):
        self.logger = logging.getLogger(__name__)
        self.auth_map = server.auth_map
        SimpleJSONRPCRequestHandler.__init__(self, request, client_address, server)
        self.client_digest = client_digest

    def do_POST(self):

        if self.auth_map != None:
            if self.headers.has_key('authorization') and self.headers['authorization'].startswith('Basic '):
                authenticationString = base64.b64decode(self.headers['authorization'].split(' ')[1])
                if authenticationString.find(':') != -1:
                    username, password = authenticationString.split(':', 1)
                    self.logger.info('Got request from %s:%s' % (username, password))

                    if self.auth_map.has_key(username) and self.verifyPassword(username, password):
                        return SimpleJSONRPCRequestHandler.do_POST(self)
                    else:
                        self.logger.error('Authentication failed for %s:%s' % (username, password))
            
            self.logger.error('Authentication failed')
            self.send_response(401)
            self.end_headers()
            return False

        return SimpleJSONRPCRequestHandler.do_POST(self)

    def verifyPassword(self, username, givenPassword):
        return self.auth_map[username] == givenPassword
   
class MeasurementService(object):
    
    def __init__(port, config, auth_map):
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.config = config
        self.auth_map = auth_map

    def status(self, measurement_id):
        try:
            self.logger.info('Got status request for measurement_id %d' % (measurement_id))
            
            retrieve = Retrieve(measurement_id, self.key, sess=self.sess)
            atlas_status = retrieve.check_status()
            return self.to_servicestatus(atlas_status)
        except Exception, e:
            self.logger.error('Got exception for status with measurement_id %d' % measurement_id, exc_info=True)
            raise e

    def run(self):
        server = SimpleForkingJSONRPCServer(('', self.port), requestHandler=SecuredHandler, auth_map=self.auth_map)

        server.register_function(self.status, 'status')

        self.logger.info('Starting service on port: %d' % self.port)
        server.serve_forever()

def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

def load_auth(auth_file):
    auth_map = {}
    
    with open(auth_file) as f:
        for line in f:
            (user, password) = line.strip().split(':')
            auth_map[user] = password
    
    return auth_map

if __name__ == '__main__':
    
    if len(sys.argv) != 4:
        sys.stderr.write('Usage: <port> <config> <auth_file>\n')
        sys.exit(1)

    port = int(sys.argv[1])
    config_file = sys.argv[2]
    auth_file = sys.argv[3]
    
    setup_logging()
    auth_map = load_auth(auth_file)
    config = load_config(config_file)

    service = MeasurementService(port, config, auth_map)
    service.run()
