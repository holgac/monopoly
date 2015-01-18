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

class GameState:
	uninitialized = 0
	starting = 1
	player_turn = 2
	terminated = 3
	buy_property_prompt = 4
	income_tax_prompt = 5
	open_card_prompt = 6
	in_jail = 7
	not_in_jail = 8
	game_over = 9
	state_names = {
		uninitialized:'uninitialized',
		starting:'starting',
		player_turn:'player_turn',
		terminated:'terminated',
		buy_property_prompt:'buy_property_prompt',
		income_tax_prompt:'income_tax_prompt',
		open_card_prompt: 'open_card_prompt',
		in_jail: 'in_jail',
		not_in_jail: 'not_in_jail'
		game_over: 'game_over'
	}
