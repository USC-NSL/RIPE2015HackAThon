#!/usr/bin/python -u
import socket
import select
import sys
import os
import threading
import traceback
import resolver
import json

DATA_TEMPLATE = 'DATA\t%s\t%s\t%s\t%s\t%s\t%s\n'
TTL = '5'
HOSTNAME_BASE = None

def read_conffile(filename):
    try:
        with open(filename,'r') as fh:
            conf = json.load(fh)
            return conf
    except Exception, e:
        raise Exception('Error reading config file: %s' % filename, e)

def config_socket(socket_file):
     # Make sure the socket does not already exist
    try:
        os.unlink(socket_file)
    except OSError:
        if os.path.exists(socket_file):
            raise

def process(data, conn, resolver):
    line = data.strip()
    print(line)

    if line == 'HELO\t1' or line == 'HELO\t2' or line == 'HELO\t3':
        print('SEnding OK')
        conn.sendall('OK\t\n')
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
    hostname = qname
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
            conn.sendall(response)
            
        if qtype == 'ANY' or qtype == 'SOA':
            response = DATA_TEMPLATE % (qname, qclass, 'SOA', TTL, qid, 'ns1.m.ripeatlasdns.net\troot.ripeatlasdns.net\t2008080300\t1800\t3600\t604800\t3600')
            conn.sendall(response)
    else:
        conn.sendall('FAIL\n')
        return
        
    conn.sendall('END\n')

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

    config = read_conffile(sys.argv[1])
    sys.stderr.write('Finished reading configuration\n')

    socket_file = config['socket-file']
    HOSTNAME_BASE = config['hostname-base']
    config_socket(socket_file)
   
    resolver = resolver.Resolver(config)

    # Create a UDS socket
    socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    # Bind the socket to the port
    print >>sys.stderr, 'listening on %s' % socket_file
    socket_server.bind(socket_file)
    socket_server.listen(5)

    sys.stderr.write('Server started\n')
 
    connection_list = [socket_server]
    file_map = {}

    try:
        while 1:
            try:
                rlist, wlist, xlist = select.select(connection_list, [], [], 5000)
                print('%s %s %s' % (rlist, wlist, xlist))
                for sock in rlist:
                    
                    if sock == socket_server:
                        conn, addr = sock.accept()
                        connection_list.append(conn)
                    else:
                        conn = sock

                    if conn not in file_map:
                        file_map[conn] = conn.makefile()                            
                    
                    f = file_map[conn]
                    data = f.readline()
                    print('data: %s' % data)
                    
                    if not data:
                        conn.close()
                        connection_list.remove(conn)
                    else:
                        process(data, conn, resolver)
            except (KeyboardInterrupt, SystemExit):
                break
            except:
                traceback.print_exc(file=sys.stderr) 
                pass
    finally:
        sys.stderr.write('Shutting down\n')
        socket_server.close()
