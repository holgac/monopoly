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


import re, itertools, json
import cards, states

class Event:
	class EventType:
		add_player = 0
		start_game = 1
		roll_die_for_the_first_time = 2
		roll_die = 3
		buy_property_response = 4
		income_tax_response = 5
		open_card = 6
		quit = 7
		roll_die_in_jail = 8
		detect_state = 9
		get_holdings = 10
	def __init__(self, event_type):
		self.event_type = event_type

# TODO: send new GameState along with responses
class EventResponse:
	def __init__(self, event, response, success=True, new_state=None, next_player=None):
		self.event = event
		self.response = response
		self.success = success
		self.new_state = new_state
		self.next_player = next_player
	def __str__(self):
		return 'EventResponse:\n\tFor:{0}\n\tsuccess:{1}\n\tNew state:{2}\n\tNext Player:{3}\n\tresponse:{4}'.format(
			self.event.__class__.__name__, self.success, states.GameState.state_names[self.new_state],
			json.dumps(self.next_player), json.dumps(self.response))

class AddPlayerEvent(Event):
	def __init__(self, player_name):
		Event.__init__(self, Event.EventType.add_player)
		self.player_name = player_name
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.uninitialized)
		monopoly.players.append(self.player_name)
		return EventResponse(self, None)
	def __str__(self):
		return 'StartGameEvent'

class RemovePlayerEvent(Event):
	def __init__(self, player_name):
		Event.__init__(self, Event.EventType.add_player)
		self.player_name = player_name
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.uninitialized)
		del monopoly.players[monopoly.players.index(self.player_name)]
		return EventResponse(self, None)
	def __str__(self):
		return 'StartGameEvent'


class StartGameEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.start_game)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.uninitialized)
		monopoly.expect_input('How many players?')
		monopoly.write(str(len(monopoly.players)))
		for player, idx in itertools.izip(monopoly.players, xrange(1, len(monopoly.players)+1)):
			monopoly.expect_input('Player {0}\'s name:'.format(idx))
			monopoly.write(player)
		monopoly.state = states.GameState.starting
		return EventResponse(self, None)
	def __str__(self):
		return 'StartGameEvent'

class RollDieForTheFirstTimeEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_die_for_the_first_time)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.starting)
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
			monopoly.state = states.GameState.player_turn
		# consume last message
		monopoly.get_line()
		return EventResponse(self,die,success)

class DetectStateEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.detect_state)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.player_turn)
		if monopoly.peek_line() == monopoly.players[monopoly.next_player] + ' rolled doubles.  Goes again':
			monopoly.get_line()
		monopoly.expect_input('{0} \({1}\) .*'.format(
			monopoly.players[monopoly.next_player],
			monopoly.next_player+1), True)
		re_template = '\(This is your ([0-3])[a-z \(\)]* turn in JAIL\)$'
		inp = monopoly.peek_line()
		# self.jail_turn_count = 0
		m = re.match(re_template, inp)
		if m:
			monopoly.jail_turn_count = int(m.group(1))
			monopoly.get_line()
			monopoly.state = states.GameState.in_jail
		else:
			monopoly.state = states.GameState.not_in_jail
		monopoly.expect_input('-- Command:')
		return EventResponse(self, None)

class GetHoldingsEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.get_holdings)
	def run(self, monopoly):
		monopoly.expect_state([states.GameState.not_in_jail, states.GameState.in_jail])
		response = {'holdings':{}}
		monopoly.write('holdings')
		for p in monopoly.players:
			monopoly.expect_input('Whose holdings do you want to see?')
			monopoly.write(p)
			p_holdings = {}
			monopoly.expect_input(p + '\'s \([0-9]+\) holdings \(Total worth: \$[0-9]+\):', True)
			p_holdings['balance'] = monopoly.get_line()
			if monopoly.peek_line() == 'Name	  Own	  Price Mg # Rent':
				monopoly.get_line()
			p_properties = []
			while monopoly.peek_line() != 'Whose holdings do you want to see?':
				p_properties.append(monopoly.get_line())
			p_holdings['properties'] = p_properties
			response['holdings'][p] = p_holdings
		monopoly.expect_input('Whose holdings do you want to see?')
		monopoly.write('done')
		monopoly.state = states.GameState.player_turn
		return EventResponse(self, response)


class RollDieEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_die)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.not_in_jail)
		monopoly.write('roll')
		# get "roll is x, y"
		die = monopoly.get_line().split()[2:]
		# print die
		# get rid of comma and make tuple
		die = (int(die[0][:-1]), int(die[1]))
		monopoly.last_die = die
		if monopoly.peek_line() == 'That\'s 3 doubles.  You go to jail':
			response = {'die':die}
			monopoly.end_turn()
			monopoly.state = states.GameState.player_turn
		else:
			response = monopoly.handle_tile_visit()
			response['die'] = die
		return EventResponse(self, response)

class RollDieInJailEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.roll_die_in_jail)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.in_jail)
		monopoly.write('roll')
		# get "roll is x, y"
		die = monopoly.get_line().split()[2:]
		# print die
		# get rid of comma and make tuple
		die = (int(die[0][:-1]), int(die[1]))
		monopoly.last_die = die
		response = {}
		if die[0] == die[1]:
			monopoly.expect_input('Double roll gets you out.')
			monopoly.just_got_out_of_jail = True
			response = monopoly.handle_tile_visit()
			response['success'] = True
			response['die'] = die
		elif monopoly.jail_turn_count == 3:
			monopoly.expect_input('Sorry, that doesn\'t get you out')
			monopoly.expect_input('It\'s your third turn and you didn\'t roll doubles.  You have to pay $50')
			monopoly.just_got_out_of_jail = True
			response = monopoly.handle_tile_visit()
			response['success'] = True
			response['die'] = die
		else:
			monopoly.expect_input('Sorry, that doesn\'t get you out')
			monopoly.end_turn()
			response['success'] = False
			monopoly.state = states.GameState.player_turn
		return EventResponse(self, response)

class BuyPropertyResponseEvent(Event):
	def __init__(self, response):
		Event.__init__(self, Event.EventType.buy_property_response)
		self.response = response
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.buy_property_prompt)
		if self.response:
			monopoly.write('yes')
			monopoly.state = states.GameState.player_turn
			monopoly.end_turn()
		else:
			raise AssertionError('Unhandled state response!')
		return EventResponse(self, None, True)

class IncomeTaxResponseEvent(Event):
	def __init__(self, use_percentage):
		Event.__init__(self, Event.EventType.income_tax_response)
		self.use_percentage = use_percentage
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.income_tax_prompt)
		if self.use_percentage:
			monopoly.write('10%')
		else:
			monopoly.write('200')
		message = monopoly.get_line()
		msg = monopoly.peek_line()
		re_template = 'Good guess\. .*'
		if re.match(re_template, msg):
			monopoly.get_line()
		monopoly.state = states.GameState.player_turn
		monopoly.end_turn()
		return EventResponse(self, {'message':message}, True)

class OpenCardEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.open_card)
	def run(self, monopoly):
		monopoly.expect_state(states.GameState.open_card_prompt)
		re_template = '[\-]+'
		inp = monopoly.get_line()
		assert(re.match(re_template, inp))
		message = []
		inp = monopoly.get_line()
		while not re.match(re_template, inp):
			message.append(inp)
			inp = monopoly.get_line()
		if cards.Cards.has_prompt(message):
			response = monopoly.handle_tile_visit(True)
			response['message'] = message
			response['state_name'] = states.GameState.state_names[monopoly.state]
			return EventResponse(self, response, True)
		else:
			response = {'message':message}
			if cards.Cards.extra_msg(message):
				re_template = 'You had ([0-9]+) Houses and ([0-9]+) Hotels, so that cost you \$([0-9]+)'
				st = monopoly.get_line()
				m = re.match(re_template, st)
				assert(m)
				response['message'].append(st)
				if int(m.group(3)) == 0:
					# consume monop admiring our luck
					monopoly.get_line()
			if monopoly.peek_line() == 'You pass === GO === and get $200':
				monopoly.get_line()
				response['passed_go'] = True
			monopoly.end_turn()
			monopoly.state = states.GameState.player_turn
			return EventResponse(self, response, True)

class QuitEvent(Event):
	def __init__(self):
		Event.__init__(self, Event.EventType.quit)

	def run(self, monopoly):
		monopoly.expect_state([states.GameState.not_in_jail, states.GameState.in_jail])
		monopoly.write('quit')
		monopoly.expect_input('Do you all really want to quit?')
		monopoly.write('yes')
		monopoly.proc.wait()
		monopoly.state = states.GameState.terminated
		return EventResponse(self, None)

