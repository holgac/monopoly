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

class GameState:
	uninitialized = 0
	starting = 1
	player_turn = 2

class Event:
	class EventType:
		start_game = 0
		roll_die_first_time = 1
	def __init__(self, event_type):
		self.event_type = event_type
	@staticmethod
	def create_event(event_type):
		# Factory method with event registration would be nice
		if event_type == Event.EventType.start_game:
			return StartGameEvent()
		if event_type == Event.EventType.roll_die_first_time:
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
		monopoly.expect_state(GameState.uninitialized)
		monopoly.players = self.players
		monopoly.expect_input('How many players? ')
		monopoly.write(str(len(self.players)))
		for player, idx in itertools.izip(monopoly.players, xrange(1, len(monopoly.players)+1)):
			monopoly.expect_input('Player {0}\'s name: '.format(idx))
			monopoly.write(player)
		monopoly.state = GameState.starting
		return EventResponse(self, None)
	def __str__(self):
		return 'StartGameEvent'

class RollDieForTheFirstTimeEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_die_first_time)
	def run(self, monopoly):
		monopoly.expect_state(GameState.starting)
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
			monopoly.state = GameState.player_turn
		# consume last message
		monopoly.get_line()
		return EventResponse(self,die,success)

class RollDieEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_dice)
	def run(self, monopoly):
		monopoly.expect_state(GameState.player_turn)
		# consume 'command: '
		monopoly.get_line()
		monopoly.write('roll')
		# get "roll is x, y"
		die = monopoly.get_line().split()[2:]
		# get rid of comma and make tuple
		die = (int(die[0][:-1]), int(die[1]))


