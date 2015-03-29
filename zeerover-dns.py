#!/usr/bin/env python
### adapted from : http://thepacketgeek.com/scapy-p-09-scapy-and-dns/
"""
Adapted from Emile Aben's scapy-dns-ninja DNS server. 
https://github.com/emileaben/scapy-dns-ninja
"""
from scapy.all import *
import sys
import json
import traceback
import resolver
import socket

def read_conffile(filename):
    try:
        with open(filename,'r') as fh:
            conf = json.load(fh)
            return conf
    except Exception, e:
        raise Exception('Error reading config file: %s' % filename, e)

def generate_response(pkt, dest, proto):
   ptype='A'

   if proto=='v6':
      ptype='AAAA'
   elif proto=='cname':
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
            an=DNSRR(rrname=pkt[DNS].qd.qname, type=ptype, ttl=5, rdata=dest),
      )
   return resp

def record(src, hostname, proto, dest_ip):
   ''' write we sent this pkt somewhere '''
   return "src=%s list=%s proto=%s dest=%s" % (src, hostname, proto, dest_ip)

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

class DNSResponder:

    def __init__(self, config):
        self.config = config
        self.resolver = resolver.Resolver(config) 
        
        self.server_ip = config['server-ip']
        self.hostname_base = config['hostname-base']

    def get_response(self, pkt):

        conf = self.config
        resolver = self.resolver
        server_ip = self.server_ip
        hostname_base = self.hostname_base
 
        if (DNS not in pkt or pkt[DNS].opcode != 0L or pkt[DNS].ancount != 0 or pkt[IP].src == server_ip):
            #sys.stderr.write("no qd.qtype in this dns request?!\n") #TODO figure out what to log here?
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
            if hostname[-1] == '.':
                hostname = hostname[:-1]

            sys.stderr.write('query src: %s query: %s\n' % (pkt[IP].src, hostname)) 
            if not hostname.endswith(hostname_base):
                return

            dest = resolver.resolve(hostname) 
            if not is_ip(dest): #return CNAME is this is a hostname
                pkt_proto = 'cname'        
            

            """
            Build response
            """
            resp = generate_response(pkt, dest, pkt_proto)
            send(resp, verbose=0)

            return record(pkt[IP].src, hostname, pkt_proto, dest)
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

    dns_filter = "udp port 53 and ip dst %s and not ip src %s" % (conf['server-ip'], conf['server-ip'])
    sniff(filter=dns_filter, store=0, prn=responder.get_response)
