import time
from sqlalchemy import *
import pylru
import logging

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

class Resolver:

    def __init__(self, config):

        self.logger = logging.getLogger()
        self.address = config['db.url']
        self.uniq_host = config['hostname-base']
      
        self.engine = create_engine(self.address, pool_recycle=3600, pool_size=10)
      
        cache_size = config.get('cache-size', 100)
        self.cache = pylru.lrucache(cache_size)
 
        #add auto reconnect
        self.connection = self.engine.connect()
        metadata = MetaData(bind=self.connection)
        self.m_table = Table('measurement', metadata, autoload=True)

    def resolve(self, hostname):

        if hostname in self.cache:
            measurement = self.cache[hostname]
        else:
            results = self.connection.execute(self.m_table.select().where(self.m_table.c.hostname==hostname))
            measurement_row = results.first() #implicit close
            measurement = dict(measurement_row) #copy the row data to cache
            
            dests = measurement['destination_list']
            dest_list = dests.split(',')
            measurement['dest_list'] = dest_list

            self.cache[hostname] = measurement 
 
        timestamp = int(time.time())
        dest_list = measurement['dest_list']      
 
        if measurement['measurement_start_time'] == None:
            self.logger.info("First request for %s" % hostname)
            
            update = self.connection.execute(self.m_table.update().where(self.m_table.c.id==measurement['id']), {"measurement_start_time": timestamp})
            #TODO what to do here if this fails??

            return dest_list[0]
        else: 
            current_time = timestamp
            first_time = measurement['measurement_start_time']
            interval = measurement['measurement_interval']
            difference = current_time - first_time

            slot = (difference/interval) % len(dest_list)
            
            return dest_list[slot]
