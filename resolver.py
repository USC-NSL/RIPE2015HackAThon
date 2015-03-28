import time
from sqlalchemy import *

class Resolver:

	def __init__(self, config):
		self.address = config['db.url']
		self.uniq_host = config['hostname-base']

		self.engine = create_engine(self.address)
     	self.connection = engine.connect()
		metadata = MetaData(bind=connection)
		self.users = Table('measurement', metadata, autoload=True)

	def resolve(self, hostname):

		u = self.connection.execute(self.users.select().where(users.c.hostname==hostname))

		timestamp = int(time.time())
		for row in u:
			dests = row['destination_list']
			if row['measurement_start_time'] == 99:
				print "First time probing this hostname"
				
                update = self.connection.execute(self.users.update().where(self.users.c.id==row['id']), {"measurement_start_time": timestamp})
                #TODO what to do here if this fails??				

                dest_list=dests.split(',')
                #TODO cache here lol. 
				return dest_list[0]
			else: 
				current_time=timestamp
				first_time=int(row['measurement_start_time'])
				interval=int(row['measurement_interval'])
				difference=current_time - first_time

				dest_list=dests.split(',')
                slot = (difference/interval) % len(dest_list)
				return dest_list[slot]
