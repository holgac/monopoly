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
import cards
import states


class Event:
    class EventType:
        start_game = 0
        roll_die_first_time = 1
        roll_die = 2
        buy_property = 3
        income_tax = 4
        open_card = 5
        quit_game = 6
    def __init__(self, event_type):
        self.event_type = event_type
    @staticmethod
    def create_event(event_type):
        # Factory method with event registration would be nice
        if event_type == Event.EventType.start_game:
            return StartGameEvent()
        if event_type == Event.EventType.roll_die_first_time:
            return RollDiceEvent()

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
            self.event.__class__.__name__, self.success, GameState.state_names[self.new_state],
            json.dumps(self.next_player), json.dumps(self.response))

class StartGameEvent(Event):
    def __init__(self, players):
        Event.__init__(self, Event.EventType.start_game)
        self.players = players
    def run(self, monopoly):
        monopoly.expect_state(states.GameState.uninitialized)
        monopoly.players = self.players
        monopoly.expect_input('How many players?')
        monopoly.write(str(len(self.players)))
        for player, idx in itertools.izip(monopoly.players, xrange(1, len(monopoly.players)+1)):
            monopoly.expect_input('Player {0}\'s name:'.format(idx))
            monopoly.write(player)
        monopoly.state = states.GameState.starting
        return EventResponse(self, None)
    def __str__(self):
        return 'StartGameEvent'

class RollDieForTheFirstTimeEvent(Event):
    def __init__(self):
        Event.__init__(self, Event.EventType.roll_die_first_time)
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

class RollDieEvent(Event):
    def __init__(self):
        Event.__init__(self, Event.EventType.roll_die)
    def run(self, monopoly):
        monopoly.expect_state(states.GameState.player_turn)
        monopoly.expect_input('{0} \({1}\) .*'.format(
            monopoly.players[monopoly.next_player],
            monopoly.next_player+1), True)
        monopoly.expect_input('-- Command:')
        monopoly.write('roll')
        # get "roll is x, y"
        die = monopoly.get_line().split()[2:]
        # print die
        # get rid of comma and make tuple
        die = (int(die[0][:-1]), int(die[1]))
        monopoly.last_die = die
        response = monopoly.handle_tile_visit()
        response['die'] = die
        return EventResponse(self, response)

class BuyPropertyResponseEvent(Event):
    def __init__(self, response):
        Event.__init__(self, Event.EventType.buy_property)
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
        Event.__init__(self, Event.EventType.income_tax)
        self.use_percentage = use_percentage
    def run(self, monopoly):
        monopoly.expect_state(states.GameState.income_tax_prompt)
        if self.use_percentage:
            monopoly.write('10%')
        else:
            monopoly.write('200')
        message = monopoly.get_line()
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
        print 'card: \t' + str(message)
        if cards.Cards.has_prompt(message):
            response = monopoly.handle_tile_visit()
            response['message'] = message
            monopoly.state = states.GameState.player_turn
            return EventResponse(self, response, True)
        else:
            for _ in xrange(cards.Cards.extra_msg_count(message)):
                monopoly.get_line()
            monopoly.end_turn()
            monopoly.state = states.GameState.player_turn
            return EventResponse(self, {'message':message}, True)

class QuitEvent(Event):
    def __init__(self):
        Event.__init__(self, Event.EventType.quit_game)

    def run(self, monopoly):
        monopoly.expect_state(states.GameState.player_turn)
        # TODO: <player> (<no>) on <place>
        monopoly.get_line()
        monopoly.expect_input('-- Command:')
        monopoly.write('quit')
        monopoly.expect_input('Do you all really want to quit?')
        monopoly.write('yes')
        monopoly.proc.wait()
        monopoly.state = states.GameState.terminated
        return EventResponse(self, None)
