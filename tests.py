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

import json, httplib, re, datetime, sys, time
import unittest
import monopoly, events

class CreationTests(unittest.TestCase):
	verbose = True
	def setUp(self):
		self.start_time = time.time()
	def tearDown(self):
		t = time.time() - self.start_time
		t = float(str(t))
		t = float(int(t*1000)/1000.0)
		sys.stdout.write(' time: ' + str(t) + '  status: ')
		sys.stdout.flush()
	def test_creation(self):
		m = monopoly.Monopoly()
		self.assertTrue(m.state == events.GameState.uninitialized)
		player_names = ['Mal', 'Zoe', 'Wash', 'Inara', 'Jayne',
			'Kaylee', 'Simon', 'River', 'Shepherd']
		e = events.StartGameEvent(player_names)
		r = m.handle_event(e)
		self.assertTrue(r.event == e)
		self.assertTrue(r.success == True)
		self.assertTrue(r.response == None)
		self.assertTrue(m.state == events.GameState.starting)
		roll_success = False
		while not roll_success:
			e = events.RollDieForTheFirstTimeEvent()
			r = m.handle_event(e)
			self.assertTrue(r.event == e)
			roll_success = r.success
		for p in player_names:
			self.assertTrue(p in r.response)
	def test_naber(self):
		self.assertTrue(3 == 3)
		self.assertTrue(4 < 3)


if __name__ == '__main__':
	import os
	loader = unittest.TestLoader()
	ln = lambda f: getattr(CreationTests, f).im_func.func_code.co_firstlineno
	lncmp = lambda a, b: cmp(ln(a), ln(b))
	loader.sortTestMethodsUsing = lncmp
	unittest.main(testLoader=loader, verbosity=2)
