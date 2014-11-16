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
import itertools, json, traceback,monopoly


class GameState:
	uninitialized = 0
	starting = 1
	player_turn = 2
	terminated = 3
	buy_property_prompt = 4

class Board:
	class TileType:
		regular = 0
		go = 1
		chest = 2
		income_tax = 3
		just_visiting = 4
		free_parking = 5
		go_to_jail = 6
	class TilePositions:
		chests = [2, 7, 17, 22, 33, 36]
		go = 0
		income_tax = 4
		just_visiting = 10
		free_parking = 20
		go_to_jail = 30

	tiles = ["=== GO ===", "Mediterranean ave. (P)", "Community Chest i",
		"Baltic ave. (P)", "Income Tax", "Reading RR", "Oriental ave. (L)",
		"Chance i", "Vermont ave. (L)", "Connecticut ave. (L)", "Just Visiting",
		"St. Charles pl. (V)", "Electric Co.", "States ave. (V)", "Virginia ave. (V)",
		"Pennsylvania RR", "St. James pl. (O)", "Community Chest ii",
		"Tennessee ave. (O)", "New York ave. (O)", "Free Parking",
		"Kentucky ave. (R)", "Chance ii", "Indiana ave. (R)", "Illinois ave. (R)",
		"B&O RR", "Atlantic ave. (Y)", "Ventnor ave. (Y)", "Water Works",
		"Marvin Gardens (Y)", "GO TO JAIL", "Pacific ave. (G)",
		"N. Carolina ave. (G)", "Community Chest iii", "Pennsylvania ave. (G)",
		"Short Line RR", "Chance iii", "Park place (D)", "Luxury Tax",
		"Boardwalk (D)", "JAIL"]

	@staticmethod
	def get_tile_type(tile_name):
		try:
			idx = Board.tiles.index(tile_name)
			if idx in Board.TilePositions.chests:
				return Board.TileType.chest
			if idx == Board.TilePositions.go:
				return Board.TileType.go
			if idx == Board.TilePositions.income_tax:
				return Board.TileType.income_tax
			if idx == Board.TilePositions.just_visiting:
				return Board.TileType.just_visiting
			if idx == Board.TilePositions.free_parking:
				return Board.TileType.free_parking
			if idx == Board.TilePositions.go_to_jail:
				return Board.TileType.go_to_jail
			return Board.TileType.regular
		except ValueError, e:
			raise AssertionError('No tile named' + tile_name)

class Event:
	class EventType:
		start_game = 0
		roll_die_first_time = 1
		roll_die = 1
	def __init__(self, event_type):
		self.event_type = event_type
	@staticmethod
	def create_event(event_type):
		# Factory method with event registration would be nice
		if event_type == Event.EventType.start_game:
			return StartGameEvent()
		if event_type == Event.EventType.roll_die_first_time:
			return RollDiceEvent()


class Event:
    class EventType:
        start_game = 0
        roll_dice_first_time = 1
        quit_game = 2

    def __init__(self, event_type):
        self.event_type = event_type

    @staticmethod
    def create_event(event_type):
        # Factory method with event registration would be nice
        if event_type == Event.EventType.start_game:
            return StartGameEvent()
        if event_type == Event.EventType.roll_dice_first_time:
            return RollDiceEvent()
        if event_type == Event.EventType.quit_game:
            return QuitEvent()

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
        for player, idx in itertools.izip(monopoly.players, xrange(1, len(monopoly.players) + 1)):
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
		Event.__init__(self, Event.EventType.roll_die)
	def run(self, monopoly):
		monopoly.expect_state(GameState.player_turn)
		# consume 'player (<cash>) <tile>'
		monopoly.get_line()
		# consume 'command: '
		monopoly.get_line()
		monopoly.write('roll')
		# get "roll is x, y"
		die = monopoly.get_line().split()[2:]
		# print die
		# get rid of comma and make tuple
		die = (int(die[0][:-1]), int(die[1]))
		re_template = "That puts you on ([A-Za-z \(\)\.\=&]+)"
		inp = monopoly.get_line()
		m = re.match(re_template, inp)
		assert(m)
		tile_type = Board.get_tile_type(m.group(1))
		response = {}
		response['die'] = die
		response['tile_type'] = tile_type
		response['location'] = m.group(1)
		next_state = GameState.player_turn
		# TODO: fill
		if tile_type == Board.TileType.regular:
			re_template = 'That would cost \$([0-9]+)'
			inp = monopoly.get_line()
			m = re.match(re_template, inp)
			# TODO: handle owned property
			assert(m)
			response['cost'] = int(m.group(1))
			monopoly.expect_input('Do you want to buy? ')
			monopoly.state = GameState.buy_property_prompt
			return EventResponse(self, response)
		raise AssertionError('Unhandled tile type: ' + json.dumps(response))
		# elif tile_type == Board.TileType.go:
		# 	pass
		# elif tile_type == Board.TileType.chest:
		# 	pass
		# elif tile_type == Board.TileType.income_tax:
		# 	pass
		# elif tile_type == Board.TileType.just_visiting:
		# 	pass
		# elif tile_type == Board.TileType.free_parking:
		# 	pass
		# elif tile_type == Board.TileType.go_to_jail:
		# 	pass

    def __init__(self):
        Event.__init__(self, Event.EventType.roll_dice_first_time)

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
            monopoly.next_player = first_player_idx
            monopoly.state = GameState.player_turn
        # consume last message
        monopoly.get_line()
        return EventResponse(self, die, success)


class RollDiceEvent(Event):
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

class QuitEvent(Event):
    def __init__(self):
        Event.__init__(self, Event.EventType.quit_game)

    def run(self, monopoly):
        monopoly.expect_state(GameState.player_turn)
        monopoly.write('quit')
        monopoly.get_line()
        monopoly.write('yes')
        monopoly.proc.wait()
        monopoly.state = GameState.terminated
        return EventResponse(self, None)
