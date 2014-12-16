# Monopoly
# Copyright (C) 2014 Emre Deniz Ozer & Huseyin Muhlis Olgac

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import inspect, re, sys, threading, json, socket, traceback
import monopoly, events

class GameFactory(object):
	def __init__(self, game_class):
		self.games = {}
		self.last_id = -1
		self.game_class = None
	def get_instance(self, game_id):
		return self.games[game_id]
	def create_instance(self, Game):
		self.last_id += 1
		g = self.game_class()
		self.games[self.last_id] = g
		return (self.last_id, g)
	def destroy_instance(self, game_id):
		self.games[game_id].kill()
		del self.games[game_id]

class EventFactory(object):
	def __init__(self):
		self.events = {}
	def register_event(self, event_type, event_class):
		self.events[event_type] = event_class
	def get_event_class(self, event_type):
		return self.events[event_type]

class Agent(threading.Thread):
	def __init__(self, connection, client_address, game_factory, event_factory):
		threading.Thread.__init__(self)
		self.connection = connection
		self.client_address = client_address
		self.game_factory = game_factory
		self.event_factory = event_factory
	def play_game(self):
		# message structure:
		# {"game":"game_id", "event":"roll_die", "params":[]}
		try:
			print >>sys.stderr, 'connection from', self.client_address
			data = self.connection.recv(65536)
			self.monop = None
			if data:
				req = json.loads(data)
				self.game_id = req['game']
				if self.game_id:
					self.monop = self.game_factory.get_instance(self.game_id)
				else:
					self.game_id, self.monop = self.game_factory.create_instance(monopoly.Monopoly)
			else:
				return

			# Receive the data in small chunks and retransmit it
			while True:
				data = self.connection.recv(65536)
				if data:
					req = json.loads(data)
					print >>sys.stderr, 'sending data back to the client'
					self.connection.sendall(json.dumps(req))
				else:
					print >>sys.stderr, 'no more data from', self.client_address
					break
		except Exception, e:
			traceback.print_exc()
			raise e
		finally:
			# Clean up the connection
			self.connection.close()

	def run(self):
		print "my thread ", id(threading.current_thread), " is started"
		print "my thread ", id(threading.current_thread), " is running"
		self.play_game()
		print "my thread ", id(threading.current_thread), " is stopped"


class GameServer(object):
	def __init__(self):
		self.event_factory = EventFactory()
		cpred = lambda c: inspect.isclass(c) and c.__module__ == 'events'
		event_classes = inspect.getmembers(sys.modules['events'], cpred)
		camel_to_underscore_s = lambda name: re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
		camel_to_underscore = lambda name: re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_to_underscore_s(name)).lower()
		event_base_class = None
		for event_name, event_class in event_classes:
			if event_name == 'Event':
				event_base_class = event_class
		for event_name, event_class in event_classes:
			class_hierarchy = inspect.getmro(event_class)
			if len(class_hierarchy) == 2 and class_hierarchy[1] == event_base_class:
				name = camel_to_underscore(event_name)
				name = name[:name.rfind('_')]
				self.event_factory.register_event(name, event_class)
		self.game_factory = GameFactory(monopoly.Monopoly)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	def run(self, port=3001):
		print 'trying to run'
		# TODO: change bind address to localhost to prevent external connections
		self.sock.bind(('0.0.0.0', port))
		self.sock.listen(10)
		print 'listening'
		while True:
			connection, client_address = self.sock.accept()
			print 'a client!'
			agent = Agent(connection, client_address, None)
			agent.start()

def main():
	gs = GameServer()
	gs.run(3001)

if __name__ == '__main__':
	main()
