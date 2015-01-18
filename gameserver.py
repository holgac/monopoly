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


import inspect, re, sys, threading, json, socket
import monopoly, events, states

class GameFactory(object):
	def __init__(self, game_class):
		self.games = {}
		self.last_id = -1
		self.game_class = game_class
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
	def get_ids(self):
		keys = []
		for gameid in self.games:
			game = self.games[gameid]
			if game.state == states.GameState.uninitialized:
				keys.append(gameid)
		return keys

class EventFactory(object):
	def __init__(self):
		self.events = {}
	def register_event(self, event_type, event_class):
		self.events[event_type] = event_class
	def get_event_class(self, event_type):
		return self.events[event_type]

class Agent(threading.Thread):
	def __init__(self, connection, client_address, game_factory, event_factory, agent_no):
		threading.Thread.__init__(self)
		self.connection = connection
		self.client_address = client_address
		self.game_factory = game_factory
		self.event_factory = event_factory
		self.prelog = '[MP_AGT#{0}]:'.format(agent_no)
	def play_game(self):
		# message structure:
		# {"game":"game_id", "event":"roll_die", "params":[]}
		try:
			print self.prelog, 'Client connected!'
			data = self.connection.recv(65536)
			print self.prelog, 'Received:', data
			self.monop = None
			if data:
				print self.prelog, data
				req = json.loads(data)
				self.game_id = req['game']
				if self.game_id is not None:
					if 'delete_game' in req:
						print self.prelog, 'Deleted game with id {0}'.format(self.game_id)
						self.game_factory.destroy_instance(self.game_id)
						self.connection.sendall(json.dumps({'success':True}))
						return
					print self.prelog, 'Joined game with id {0}'.format(self.game_id)
					self.monop = self.game_factory.get_instance(self.game_id)
					if 'get_players' in req:
						print self.prelog, 'Getting players of game {0}'.format(self.game_id)
						self.connection.sendall(json.dumps({'success':True, 'players':self.monop.players}))
						return
				else:
					if 'get_list' in req:
						print self.prelog, 'Getting game list'
						self.connection.sendall(json.dumps({'success':True, 'games':self.game_factory.get_ids()}))
						return
					self.game_id, self.monop = self.game_factory.create_instance(monopoly.Monopoly)
					print self.prelog, 'Created game with id {0}'.format(self.game_id)
					resp = {'success':True,'game':self.game_id}
					self.connection.sendall(json.dumps(resp))
					data = self.connection.recv(65536)
					if not data:
						return
					req = json.loads(data)
			else:
				return
			while True:
				assert('event' in req)
				assert('params' in req)
				event_class = self.event_factory.get_event_class(req['event'])
				ev = event_class(*req['params'])
				er = self.monop.handle_event(ev)
				jresp = json.dumps(er, cls=events.EventResponse.Encoder)
				print self.prelog, jresp
				self.connection.sendall(jresp)
				data = self.connection.recv(65536)
				if not data:
					break
				req = json.loads(data)
		# except Exception, e:
		# 	traceback.print_exc()
		# 	raise e
		finally:
			# Clean up the connection
			print self.prelog, 'Quit!'

	def run(self):
		self.play_game()
		self.connection.close()
		print self.prelog, 'Thread terminated!'



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
		self.agent_no = 0
	def run(self, port=3001):
		print 'trying to run'
		# TODO: change bind address to localhost to prevent external connections
		connected = False
		while not connected:
			try:
				self.sock.bind(('0.0.0.0', port))
				connected = True
			except:
				port += 1
		self.sock.listen(10)
		print 'listening on', port
		while True:
			connection, client_address = self.sock.accept()
			print 'a client!'
			agent = Agent(connection, client_address, self.game_factory, self.event_factory, self.agent_no)
			agent.start()
			self.agent_no += 1

def main():
	gs = GameServer()
	port = 3002
	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	gs.run(port)

if __name__ == '__main__':
	main()
