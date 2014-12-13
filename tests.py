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

import sys, time, unittest
import monopoly, events, states

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

	def test_creation_and_termination(self):
		m = monopoly.Monopoly()
		self.assertTrue(m.state == states.GameState.uninitialized)
		player_names = ['Mal', 'Zoe', 'Wash', 'Inara', 'Jayne',
						'Kaylee', 'Simon', 'River', 'Shepherd']
		e = events.StartGameEvent(player_names)
		r = m.handle_event(e)
		self.assertTrue(r.event == e)
		self.assertTrue(r.success == True)
		self.assertTrue(r.response == None)
		roll_success = False
		while not roll_success:
			e = events.RollDieForTheFirstTimeEvent()
			r = m.handle_event(e)
			self.assertTrue(r.event == e)
			roll_success = r.success
		for p in player_names:
			self.assertTrue(p in r.response)

		self.assertTrue(m.state == states.GameState.player_turn)
		m.handle_event(events.DetectStateEvent())
		e = events.QuitEvent()
		q = m.handle_event(e)
		self.assertTrue(q.event == e)
		self.assertTrue(q.success == True)
		self.assertTrue(q.response == None)
		self.assertTrue(m.state == states.GameState.terminated)

class PlayingTests(unittest.TestCase):
	verbose = True
	def setUp(self):
		self.start_time = time.time()
		self.m = monopoly.Monopoly()
		player_names = ['Mal', 'Zoe', 'Wash', 'Inara', 'Jayne',
						'Kaylee', 'Simon', 'River', 'Shepherd']
		e = events.StartGameEvent(player_names)
		r = self.m.handle_event(e)
		roll_success = False
		while not roll_success:
			e = events.RollDieForTheFirstTimeEvent()
			r = self.m.handle_event(e)
			roll_success = r.success
	def tearDown(self):
		e = events.QuitEvent()
		self.m.handle_event(e)
		t = time.time() - self.start_time
		t = float(str(t))
		t = float(int(t*1000)/1000.0)
		sys.stdout.write(' time: ' + str(t) + '  status: ')
		sys.stdout.flush()
	def test_playing(self):
		turn_count = 0
		r = self.m.handle_event(events.DetectStateEvent())
		while turn_count < 20 or r.new_state != states.GameState.player_turn:
			turn_count += 1
			if r.new_state == states.GameState.player_turn:
				r = self.m.handle_event(events.DetectStateEvent())
			elif r.new_state == states.GameState.not_in_jail:
				r = self.m.handle_event(events.RollDieEvent())
			elif r.new_state == states.GameState.in_jail:
				r = self.m.handle_event(events.RollDieInJailEvent())
			elif r.new_state == states.GameState.buy_property_prompt:
				r = self.m.handle_event(events.BuyPropertyResponseEvent(True))
			elif r.new_state == states.GameState.income_tax_prompt:
				r = self.m.handle_event(events.IncomeTaxResponseEvent(False))
			elif r.new_state == states.GameState.open_card_prompt:
				r = self.m.handle_event(events.OpenCardEvent())
			else:
				# sending wrong event just to see the inputs
				r = self.m.handle_event(events.RollDieForTheFirstTimeEvent())
			print r
			print '------------------------------------'
		self.m.handle_event(events.DetectStateEvent())

def main():
	loader = unittest.TestLoader()
	# ln = lambda f: getattr(CreationTests, f).im_func.func_code.co_firstlineno
	# lncmp = lambda a, b: cmp(ln(a), ln(b))
	# loader.sortTestMethodsUsing = lncmp
	unittest.main(testLoader=loader, verbosity=2)
if __name__ == '__main__':
	main()