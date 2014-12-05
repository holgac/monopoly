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

class Cards:
	prompt_msgs = [
		'Advance to the nearest Railroad, and pay owner',
		'Advance to the nearest Utility.',
		'Go Back 3 Spaces',
		'Take a Ride on the Reading.',
		'Take a Walk on the Board Walk.',
		'Advance to Illinois Ave.',
		'Advance to St. Charles Place.',
		'Advance to Go',
		'Advance to GO'
	]
	extra_msgs = [
		'Make general repairs on all of your Property.',
		'You are Assessed for street repairs.'
	]
	@staticmethod
	def has_prompt(message_list):
		return message_list[0] in Cards.prompt_msgs
	@staticmethod
	def extra_msg(message_list):
		return message_list[0] in Cards.extra_msgs
