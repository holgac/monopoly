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

import os, subprocess, fcntl, re, json, traceback, datetime
import events, board, states

class BufferedReader:
	def __init__(self, infile):
		self.infile = infile
		self.cur_buffer = []
		self.consumed_buffer = []
	def _read_raw(self, block):
		if block:
			start_time = datetime.datetime.now()
			while True:
				try:
					diff = datetime.datetime.now() - start_time
					if diff.total_seconds() > 3:
						raise AssertionError('No input for 3 seconds!')
					return self.infile.read()
					# s =  self.infile.read()
					# print 'read ' + s
					# return s
				except IOError:
					pass
		else:
			try:
				return self.infile.read()
			except IOError:
				return None
	def _read_lines(self, block):
		raw_inp = self._read_raw(block)
		if raw_inp:
			for i in raw_inp.split('\n'):
				if i:
					self.cur_buffer.append(i.strip())
	def get_line(self, block):
		st = self.peek_line(block)
		if st:
			self.cur_buffer.pop(0)
			self.consumed_buffer.append(st)
		return st
	def peek_line(self, block):
		if self.cur_buffer:
			return self.cur_buffer[0]
		self._read_lines(block)
		if self.cur_buffer:
			return self.cur_buffer[0]
		return None


class Monopoly:
	def __init__(self):
		self.proc = subprocess.Popen(['stdbuf', '-i0', '-o0', '-e0', 'monop'],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		curfl = fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK)
		curfl = fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK | os.O_SYNC)
		self.state = states.GameState.uninitialized
		self.players = []
		self.next_player = -1
		self.inp_reader = BufferedReader(self.proc.stdout)
		self.last_die = None
		self.double_count = 0
		self.jail_turn_count = 0
		self.just_got_out_of_jail = False
		self.player_score = 0
		self.pass_go_count = 0
	def get_line(self, block=True):
		return self.inp_reader.get_line(block)
	def peek_line(self, block=True):
		return self.inp_reader.peek_line(block)

	def expect_input(self, str_to_expect, is_regex=False):
		inp = self.get_line(True)
		if is_regex:
			m = re.match(str_to_expect, inp)
			if not m:
				print 'AssertionError:\n\texpected #{0}#\n\treceived #{1}#'.format(
					str_to_expect, inp)
			assert(m)
			assert(len(m.group(0)) == len(inp))
		else:
			if str_to_expect != inp:
				print 'AssertionError:\n\texpected #{0}#\n\treceived #{1}#'.format(
					str_to_expect, inp)
			assert(str_to_expect == inp)
	def expect_state(self, state):
		if type(state) == type([]):
			if self.state not in state:
				print 'AssertionError:\n\texpected {0}\n\treceived {1}'.format(
					','.join(states.GameState.state_names[i] for i in state),
					states.GameState.state_names[self.state])
			assert(self.state in state)
		else:
			if self.state != state:
				print 'AssertionError:\n\texpected {0}\n\treceived {1}'.format(
					states.GameState.state_names[state],
					states.GameState.state_names[self.state])
			assert(self.state == state)
	def write(self, buf):
		self.proc.stdin.write(buf + '\n')
	def handle_event(self, event):
		print 'handling ' + event.__class__.__name__
		try:
			response =  event.run(self)
			response.new_state = self.state
			response.next_player = (self.next_player, self.players[self.next_player])
			response.player_score = self.player_score
			return response
		except (AssertionError, IndexError, ValueError):
			traceback.print_exc()
			self.inp_reader._read_lines(False)
			print 'Consumed lines: '
			print '#\n\t'.join(self.inp_reader.consumed_buffer[-10:])
			print 'Next lines: '
			print '#\n\t'.join(self.inp_reader.cur_buffer)
			print 'State: ' + states.GameState.state_names[self.state]
			print 'Next Player: {0} {1}'.format(self.next_player,
				self.players[self.next_player])
			# assertion errors should be more descriptive
			# raw_input()
			return events.EventResponse(event, None, False, self.state,
				(self.next_player, self.players[self.next_player]), self.player_score)
	def end_turn(self):
		if self.last_die[0] == self.last_die[1] and not self.just_got_out_of_jail:
			self.double_count += 1
			if self.double_count == 3:
				self.expect_input('That\'s 3 doubles.  You go to jail')
				self.double_count = 0
				self.next_player = (self.next_player + 1) % len(self.players)
			else:
				self.player_score += 2
				self.expect_input('{0} rolled doubles.  Goes again'.format(
					self.players[self.next_player]))
		else:
			self.double_count = 0
			self.next_player = (self.next_player + 1) % len(self.players)
		self.just_got_out_of_jail = False
		self.last_die = None
	def handle_tile_visit(self, debug=False):
		response = {}
		if self.peek_line() == 'You pass === GO === and get $200':
			self.get_line()
			response['passed_go'] = True
			self.pass_go_count += 1
			if self.pass_go_count == 5:
				self.state = states.GameState.game_over
				return
		re_template = "That puts you on ([A-Za-z \(\)\.\=&]+)"
		inp = self.get_line()
		m = re.match(re_template, inp)
		assert(m)
		tile_type = board.Board.get_tile_type(m.group(1))
		response['tile_type'] = (tile_type, board.Board.TileType.tile_names[tile_type])
		response['location'] = m.group(1)
		if tile_type == board.Board.TileType.regular:
			self.player_score += 1
			re_template = 'That would cost \$([0-9]+)'
			inp = self.get_line()
			m = re.match(re_template, inp)
			if m:
				self.player_score += 1
				response['cost'] = int(m.group(1))
				self.expect_input('Do you want to buy?')
				self.state = states.GameState.buy_property_prompt
			else:
				self.state = states.GameState.player_turn
				if inp != 'You own it.':
					re_template = 'Owned by .*'
					assert(re.match(re_template, inp))
					# TODO: what if this property is owned by us?
					re_template = 'rent is ([0-9]+)'
					inp = self.get_line()
					m = re.match(re_template, inp)
					assert(m)
					response['rent'] = int(m.group(1))
				else:
					self.player_score += 1
					response['already_owned'] = True
				self.end_turn()
		# elif tile_type == Board.TileType.go:
		# 	pass
		elif tile_type == board.Board.TileType.chest:
			self.player_score += 1
			self.state = states.GameState.open_card_prompt
		elif tile_type == board.Board.TileType.income_tax:
			self.expect_input('Do you wish to lose 10%% of your total worth or $200?')
			self.state = states.GameState.income_tax_prompt
		elif tile_type == board.Board.TileType.safe_place:
			self.player_score += 1
			self.state = states.GameState.player_turn
			self.expect_input('That is a safe place')
			self.end_turn()
		elif tile_type == board.Board.TileType.luxury_tax:
			self.player_score -= 1
			self.state = states.GameState.player_turn
			self.expect_input('You lose $75')
			self.end_turn()
		elif tile_type == board.Board.TileType.go_to_jail:
			self.player_score -= 1
			self.state = states.GameState.player_turn
			self.end_turn()
		else:
			raise AssertionError('Unhandled tile type: ' + json.dumps(response))
		return response
	def kill(self):
		try:
			self.proc.kill()
		except OSError:
			pass


def main():
	print '------------------------------------'
	print '------------------------------------'
	print '------------------------------------'
	m = Monopoly()
	print m.handle_event(events.AddPlayerEvent('ahmet'))
	print m.handle_event(events.AddPlayerEvent('mehmet'))
	print m.handle_event(events.AddPlayerEvent('ali'))
	r = m.handle_event(events.StartGameEvent())
	r = m.handle_event(events.RollDieForTheFirstTimeEvent())
	while not r.success:
		print r
		r = m.handle_event(events.RollDieForTheFirstTimeEvent())
	print r
	while True:
		if r.new_state == states.GameState.player_turn:
			r = m.handle_event(events.DetectStateEvent())
		elif r.new_state == states.GameState.not_in_jail:
			r = m.handle_event(events.GetHoldingsEvent())
			print r
			print '------------------------------------'
			r = m.handle_event(events.DetectStateEvent())
			r = m.handle_event(events.RollDieEvent())
		elif r.new_state == states.GameState.in_jail:
			r = m.handle_event(events.GetHoldingsEvent())
			print r
			print '------------------------------------'
			r = m.handle_event(events.DetectStateEvent())
			r = m.handle_event(events.RollDieInJailEvent())
		elif r.new_state == states.GameState.buy_property_prompt:
			r = m.handle_event(events.BuyPropertyResponseEvent(True))
		elif r.new_state == states.GameState.income_tax_prompt:
			r = m.handle_event(events.IncomeTaxResponseEvent(False))
		elif r.new_state == states.GameState.open_card_prompt:
			r = m.handle_event(events.OpenCardEvent())
		else:
			# sending wrong event just to see the inputs
			r = m.handle_event(events.RollDieForTheFirstTimeEvent())
		print r
		print '------------------------------------'

		# raw_input()
		if not r.success:
			raw_input()
	m.proc.kill()

if __name__ == '__main__':
	main()
