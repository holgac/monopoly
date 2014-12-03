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

class Board:
    class TileType:
        regular = 0
        chest = 2
        income_tax = 3
        safe_place = 4
        go_to_jail = 5
        luxury_tax = 6
        tile_names = {
            regular:'regular',
            chest:'chest',
            income_tax:'income_tax',
            safe_place:'safe_place',
            go_to_jail:'go_to_jail',
            luxury_tax:'luxury_tax'
        }
    class TilePositions:
        chests = [2, 7, 17, 22, 33, 36]
        income_tax = 4
        safe_places = [0, 10, 20]
        go_to_jail = 30
        luxury_tax = 38

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
            if idx == Board.TilePositions.income_tax:
                return Board.TileType.income_tax
            if idx in Board.TilePositions.safe_places:
                return Board.TileType.safe_place
            if idx == Board.TilePositions.go_to_jail:
                return Board.TileType.go_to_jail
            if idx == Board.TilePositions.luxury_tax:
                return Board.TileType.luxury_tax
            return Board.TileType.regular
        except ValueError, e:
            raise AssertionError('No tile named' + tile_name)
