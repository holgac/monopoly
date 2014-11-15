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
import events

class BufferedReader:
	def __init__(self, infile):
		self.infile = infile
		self.cur_buffer = []
		self.consumed_buffer = []
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
			# for debug purposes
			v = self.cur_buffer.pop(0)
			self.consumed_buffer.append(v)
			return v
		self._read_lines(block)
		if self.cur_buffer:
			# for debug purposes
			v = self.cur_buffer.pop(0)
			self.consumed_buffer.append(v)
			return v
		return None

class Monopoly:
	def __init__(self):
		self.proc = subprocess.Popen(['stdbuf', '-i0', '-o0', '-e0', 'monop'],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		curfl = fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stderr.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK)
		curfl = fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_GETFL)
		fcntl.fcntl(self.proc.stdout.fileno(), fcntl.F_SETFL, curfl | os.O_NONBLOCK | os.O_SYNC)
		self.state = events.GameState.uninitialized
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
			print 'Consumed lines: '
			self.inp_reader._read_lines(False)
			print '\n\t'.join(self.inp_reader.consumed_buffer)
			print 'Next lines: '
			print '\n\t'.join(self.inp_reader.cur_buffer)
			# assertion errors should be more descriptive
			return events.EventResponse(event, None, False)


def main():
	m = Monopoly()
	print m.handle_event(events.StartGameEvent(['ahmet', 'mehmet', 'cemil', 'asd', 'bsd', 'csd', 'dsd', 'esd', 'fsd']))
	r = m.handle_event(events.RollDieForTheFirstTimeEvent())
	while not r.success:
		print r
		r = m.handle_event(events.RollDieForTheFirstTimeEvent())
	print r
	print m.handle_event(events.RollDieEvent())
	m.proc.kill()

if __name__ == '__main__':
	main()