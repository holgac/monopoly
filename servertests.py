#!/usr/bin/env python

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

import unittest, socket, json

class ServerTests(unittest.TestCase):
	verbose = True
	def setUp(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		port = 3001
		server_address = ('huseyinolgac.com', port)
		self.sock.connect(server_address)
	def tearDown(self):
		self.sock.close()

	def test_game_creation(self):
		self.sock.sendall(json.dumps({'game':None}))
		resp = self.sock.recv(65536)
		self.assertTrue(resp != None)
		print resp
		resp = json.loads(resp)
		self.assertTrue(resp['success'])
		self.assertTrue('game' in resp)
		ServerTests.game_id = resp['game']
		self.assertTrue(int(resp['game']) >= 0)

	def test_adding_player(self):
		players = ['ahmet', 'mehmet', 'ali']
		for p in players:
			self.sock.sendall(json.dumps({'game':ServerTests.game_id, 'event':'add_player', 'params':[p]}))
			resp = self.sock.recv(65536)
			self.assertTrue(resp != None)
			print resp
			resp = json.loads(resp)
			self.assertTrue(resp['success'])

	def test_starting_game(self):
		self.sock.sendall(json.dumps({'game':ServerTests.game_id, 'event':'start_game', 'params':[]}))
		resp = self.sock.recv(65536)
		self.assertTrue(resp != None)
		print resp
		resp = json.loads(resp)
		self.assertTrue(resp['success'])

	def test_roll_die_first(self):
		resp = {'success':False}
		while resp['success'] == False:
			self.sock.sendall(json.dumps({'game':ServerTests.game_id, 'event':'roll_die_for_the_first_time', 'params':[]}))
			resp = self.sock.recv(65536)
			self.assertTrue(resp != None)
			print resp
			resp = json.loads(resp)
		self.assertTrue(resp['success'])

	def test_terminate(self):
		self.sock.sendall(json.dumps({'game':ServerTests.game_id, 'delete_game':True}))
		resp = self.sock.recv(65536)
		self.assertTrue(resp != None)
		print resp
		resp = json.loads(resp)
		self.assertTrue(resp['success'])

def main():
	loader = unittest.TestLoader()
	ln = lambda f: getattr(ServerTests, f).im_func.func_code.co_firstlineno
	lncmp = lambda a, b: cmp(ln(a), ln(b))
	loader.sortTestMethodsUsing = lncmp
	unittest.main(testLoader=loader, verbosity=2)
if __name__ == '__main__':
	main()
