#!/usr/bin/env python
import socket
import select
import sys
import os
import fileinput
import threading
import traceback
import resolver
import json
import logging
import logging.handlers

DATA_TEMPLATE = 'DATA\t%s\t%s\t%s\t%s\t%s\t%s\n'
TTL = '5'
HOSTNAME_BASE = None
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

def read_conffile(filename):
    try:
        with open(filename,'r') as fh:
            conf = json.load(fh)
            return conf
    except Exception, e:
        raise Exception('Error reading config file: %s' % filename, e)

def process(data, resolver):
    line = data.strip()

    if line == 'HELO\t1' or line == 'HELO\t2' or line == 'HELO\t3':
        logger.info('Got %s. Responding OK.' % line)
        sys.stdout.write('OK\t\n')
        sys.stdout.flush()
        return
   
    chunks = line.split('\t')
    
    qname = chunks[1]
    qclass = chunks[2]
    qtype = chunks[3]
    qid = chunks[4]
    remote_ip = chunks[5]
    local_ip = None
    edns_subnet = None

    if len(chunks) >= 7:  #at least atlas pipe protocol version 2
        local_ip = chunks[6]
    if len(chunks) == 8:
        edns_subnet = chunks[7]

    """
    Generate response and respond
    """
    hostname = qname.lower()
    if hostname[-1] == '.':
        hostname = hostname[:-1]

    if hostname.endswith(HOSTNAME_BASE):
 
        if qtype == 'ANY' or qtype == 'A' or qtype == 'AAAA':
            dest = resolver.resolve(hostname)
            if not is_ip(dest):
                qtype = 'CNAME'
            else:
                qtype = 'A'

            response = DATA_TEMPLATE % (qname, qclass, qtype, TTL, qid, dest)
            sys.stdout.write(response)
            
        if qtype == 'ANY' or qtype == 'SOA':
            response = DATA_TEMPLATE % (qname, qclass, 'SOA', TTL, qid, 'ns1.m.ripeatlasdns.net\troot.ripeatlasdns.net\t2008080300\t1800\t3600\t604800\t3600')
            sys.stdout.write(response)

    else:
        logger.error('FAIL for %s' % line)
        sys.stdout.write('FAIL\n')
        sys.stdout.flush()
        return
        
    sys.stdout.write('END\n')
    sys.stdout.flush()

def is_ip(dest_str):
    try:
        socket.inet_aton(dest_str)
        return True
    except socket.error:
        #try IPv6
        try:
            socket.inet_pton(socket.AF_INET6, dest_str)
            return True
        except socket.error:
            return False


if __name__ == '__main__':

    if len(sys.argv) != 2:
        sys.stderr.write('usage: config.json\n')
        sys.exit(1)

    loglevel = logging.DEBUG
 
    logger = logging.getLogger()
    logger.setLevel(loglevel)

    formatter = logging.Formatter('%(process)d %(levelname)s %(message)s')

    handler = logging.handlers.SysLogHandler(address = '/dev/log')
    handler.setLevel(loglevel)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    config = read_conffile(sys.argv[1])
    logger.debug('Finished reading configuration\n')
    
    #logging_config = config['logging']
    #dictConfig(logging_config)

    #socket_file = config['socket-file']
    HOSTNAME_BASE = config['hostname-base']
   
    resolver = resolver.Resolver(config)

    try:
        while True:
            
            line = sys.stdin.readline()
            logger.debug('Got line %s' % line)

            try:
                process(line, resolver)
            except:
                #traceback.print_exc(file=sys.stderr)
                logger.error(traceback.format_exc())
                break
    except:
        #traceback.print_exc(file=sys.stderr)
        logger.error(traceback.format_exc())

    logger.info('Exiting')
