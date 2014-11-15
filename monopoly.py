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

import pty, tty, os, threading, subprocess, sys, fcntl, re
import itertools, json, traceback

class BufferedReader:
	def __init__(self, infile):
		self.infile = infile
		self.cur_buffer = []
	def _read_raw(self, block):
		if block:
			while True:
				try:
					return self.infile.read()
					# s =  self.infile.read()
					# print 'read ' + s
					# return s
				except IOError, e:
					pass
		else:
			try:
				return self.infile.read()
			except IOError, e:
				return None
	def _read_lines(self, block):
		raw_inp = self._read_raw(block)
		if raw_inp:
			for i in raw_inp.split('\n'):
				if i:
					self.cur_buffer.append(i)
	def get_line(self, block):
		if self.cur_buffer:
			return self.cur_buffer.pop(0)
		self._read_lines(block)
		if self.cur_buffer:
			return self.cur_buffer.pop(0)
		return None

class Monopoly:
	class GameState:
		uninitialized = 0
		starting = 1
		player_turn = 2
	def __init__(self):
		self.proc = subprocess.Popen(['stdbuf', '-i0', '-o0', '-e0', 'monop'],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		curfl = fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK)
		curfl = fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK | os.O_SYNC)
		self.state = Monopoly.GameState.uninitialized
		self.players = None
		self.next_player = -1
		self.inp_reader = BufferedReader(self.proc.stdout)
	def get_line(self, block=True):
		return self.inp_reader.get_line(block)

	def expect_input(self, str_to_expect, is_regex=False):
		inp = self.get_line(True)
		if is_regex:
			assert(re.match(str_to_expect, inp) != None)
		else:
			assert(str_to_expect == inp)
	def expect_state(self, state):
		assert(self.state == state)
	def write(self, buf):
		self.proc.stdin.write(buf + '\n')
	def handle_event(self, event):
		try:
			return event.run(self)
		except AssertionError, e:
			traceback.print_exc()
			# assertion errors should be more descriptive
			return EventResponse(event, None, False)

class Event:
	class EventType:
		start_game = 0
		roll_dice = 1
	def __init__(self, event_type):
		self.event_type = event_type
	@staticmethod
	def create_event(event_type):
		# Factory method with event registration would be nice
		if event_type == Event.EventType.start_game:
			return StartGameEvent()
		if event_type == Event.EventType.roll_dice:
			return RollDiceEvent()

class EventResponse:
	def __init__(self, event, response, success=True):
		self.event = event
		self.response = response
		self.success = success
	def __str__(self):
		return 'EventResponse:\n\tFor:{0}\n\tsuccess:{1}\n\tresponse:{2}'.format(
			self.event.__class__.__name__, self.success, json.dumps(self.response))

class StartGameEvent(Event):
	def __init__(self, players):
		Event.__init__(self, Event.EventType.start_game)
		self.players = players
	def run(self, monopoly):
		monopoly.expect_state(Monopoly.GameState.uninitialized)
		monopoly.players = self.players
		monopoly.expect_input('How many players? ')
		monopoly.write(str(len(self.players)))
		for player, idx in itertools.izip(monopoly.players, xrange(1, len(monopoly.players)+1)):
			monopoly.expect_input('Player {0}\'s name: '.format(idx))
			monopoly.write(player)
		monopoly.state = Monopoly.GameState.starting
		return EventResponse(self, None)
	def __str__(self):
		return 'StartGameEvent'


class RollDieForTheFirstTimeEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_dice)
	def run(self, monopoly):
		monopoly.expect_state(Monopoly.GameState.starting)
		die = {}
		max_dice = 0
		success = True
		first_player_idx = -1
		# actually we need to do nothing here
		for player, idx in itertools.izip(monopoly.players, xrange(len(monopoly.players))):
			dice = int(monopoly.get_line().split()[-1])
			die[player] = dice
			if dice > max_dice:
				success = True
				max_dice = dice
				first_player_idx = idx
			elif dice == max_dice:
				success = False
		if success:
			monopoly.next_player = 	first_player_idx
			monopoly.state = Monopoly.GameState.player_turn
		return EventResponse(self,die,success)
def main():
	m = Monopoly()
	print m.handle_event(StartGameEvent(['ahmet', 'mehmet', 'cemil']))
	print m.handle_event(RollDieForTheFirstTimeEvent())
if __name__ == '__main__':
	main()