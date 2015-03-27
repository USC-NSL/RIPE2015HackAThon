#!/usr/bin/env python
### adapted from : http://thepacketgeek.com/scapy-p-09-scapy-and-dns/
"""
Adapted from Emile Aben's scapy-dns-ninja DNS server. 
https://github.com/emileaben/scapy-dns-ninja
"""
from scapy.all import *
import sys
from random import shuffle
import re
import json
import traceback
import os.path
import struct
import resolver

def read_conffile(filename):
    try:
        with open(filename,'r') as fh:
            conf = json.load(fh)
            return conf
    except:
        raise Exception('Error reading config file: %s' % filename)

def generate_response(pkt, dest, proto):
   ptype='A'

   if proto=='v6':
      ptype='AAAA'
   elif proto=='cnames':
      ptype='CNAME'

   resp = IP(dst=pkt[IP].src, id=pkt[IP].id)\
      /UDP(dport=pkt[UDP].sport, sport=53)\
      /DNS(id=pkt[DNS].id,
            aa=1, #we are authoritative
            qr=1, #it's a response
            rd=pkt[DNS].rd, # copy recursion-desired
            qdcount=pkt[DNS].qdcount, # copy question-count
            qd=pkt[DNS].qd, # copy question itself
            ancount=1, #we provide a single answer
            an=DNSRR(rrname=pkt[DNS].qd.qname, type=ptype, ttl=1, rdata=dest ),
      )
   return resp

def record(src, hostname, proto, dest_ip):
   ''' write we sent this pkt somewhere '''
   return "src=%s list=%s proto=%s dest=%s" % (src, hostname, proto, dest_ip)

class DNSResponder:

    def __init__(self, config):
        self.config = config
        self.resolver = resolver.Resolver(config) 
        
        self.server_ip = config['serverip']

    def get_response(self, pkt):

        conf = self.config
        resolver = self.resolver
        server_ip = self.server_ip
 
        if (DNS not in pkt or pkt[DNS].opcode != 0L or pkt[DNS].ancount != 0 or pkt[IP].src == server_ip):
            print(DNS)
            print(pkt[DNS])
            sys.stderr.write("no qd.qtype in this dns request?!\n")
            return

        try:
            
            """
            First make sure that we support this query type
            """
            pkt_proto = None
            if pkt[DNS].qd.qtype == 1:
                pkt_proto='v4'  
            elif pkt[DNS].qd.qtype == 28:
                pkt_proto='v6'  
            else: ### won't respond to non A or AAAA packet
                sys.stderr.write('Ignoring DNS query type %d\n' % pkt[DNS].qd.qtype)
                return

            """
            Find result 
            """ 
            hostname = pkt[DNS].qd.qname.lower()
            dest_ip = '8.8.8.8' #resolver.resolve(hostname) 
            

            """
            Build response
            """
            resp = generate_response(pkt, dest_ip, pkt_proto)
            send(resp,verbose=0)

            return record(pkt[IP].src, hostname, pkt_proto, dest_ip)
        except:
            sys.stderr.write('Error processing response\n')
            traceback.print_exc(file=sys.stderr)
        
if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        sys.stderr.write('usage: <config-file>\n')
        sys.exit(1)

    conf_file = sys.argv[1]

    conf = read_conffile(conf_file)
    print >>sys.stderr, "config loaded, starting server"

    responder = DNSResponder(conf)

    dns_filter = "udp port 53 and ip dst %s and not ip src %s" % (conf['serverip'], conf['serverip'])
    sniff(filter=dns_filter, store=0, prn=responder.get_response)
