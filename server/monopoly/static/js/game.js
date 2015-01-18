// Monopoly
// Copyright (C) 2014 Huseyin Muhlis Olgac

// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License along
// with this program; if not, write to the Free Software Foundation, Inc.,
// 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


// adapted from 
// http://jamesroberts.name/blog/2010/02/22/string-functions-for-javascript-trim-to-camel-case-to-dashed-and-to-underscore/
// Modified to convert the first letter to uppercase.
String.prototype.toCamel = function() {
	return this.replace(/(\_[a-z]|^[a-z])/g, function($1){return $1.toUpperCase().replace('_','');});
};


function StateBase(state) {
	var self = this;
	state.base = this;
	state.title = 'DUMMY TITLE';
	self.initialize = function(monopoly, parent_span) {
		var buttons = parent_span.find('[data-newstate]');
		$.each(buttons, function(buttonIdx) {
			// button.off('click');
			var button = buttons.eq(buttonIdx);
			button.on('click', function(event) {
				monopoly.set_state(button.data('newstate'));
			});
		});
		buttons = parent_span.find('[data-sendevent]');
		$.each(buttons, function(buttonIdx) {
			// button.off('click');
			var button = buttons.eq(buttonIdx);
			button.off('click');
			button.on('click', function(event) {
				if(button.data('eventparam') != undefined) {
					monopoly.send_event(button.data('sendevent'), button.data('eventparam'));
				} else {
					monopoly.send_event(button.data('sendevent'), []);
				}
			});
		});
		var spec = parent_span.find('[data-specialfield]');
		$.each(spec, function(speIdx) {
			var spe = spec.eq(speIdx);
			var dt = undefined;
			if(monopoly.last_msg.response) {
				dt = monopoly.last_msg.response[spe.data('fieldname')];
			}
			if(dt == undefined) {
				dt = monopoly.last_msg[spe.data('fieldname')];
			}
			var txt = '';
			if(typeof(dt) == typeof('')) {
				txt = dt;
			} else {
				txt = JSON.stringify(dt);
			}
			spe.html(txt);
		});
		spec = parent_span.find('[data-cardresponse]');
		if(spec[0]) {
			if(monopoly.last_msg.response && monopoly.last_msg.response['message']) {
				spec.eq(0).html('Card: ' + JSON.stringify(monopoly.last_msg.response['message']));
			}
		}
	};
	self.uninitialize = function(monopoly, parent_span) {
		var buttons = parent_span.find('[data-newstate]');
		$.each(buttons, function(buttonIdx) {
			buttons.eq(buttonIdx).off('click');
		});
	};

	return self;
};
function InitialState() {
	var self = this;
	StateBase(self);
	self.title = 'Welcome to Monopoly!';
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function LobbyState() {
	var self = this;
	StateBase(self);
	self.title = 'Select a game to join!';
	self.initialize = function(monopoly, parent_span) {
		self.is_active = true;
		var df = function() {
			if(self.is_active) {
				_.delay(df, 1000);
				monopoly.send_request({game:monopoly.game_id, get_list:true}, function(resp, err) {
					if(err) {
						console.log(err);
						monopoly.set_state('InitialState');
					} else if(resp.success == false) {
						console.log(resp);
						monopoly.set_state('InitialState');
					} else {
						var game_view = parent_span.find('[data-currentgames]');
						var game_str = '';
						var game_tpl = '<a href="#" data-gameid="{{GAME_ID}}">Game #{{GAME_ID}}</a><br />';
						_.each(resp.games, function(game) {
							var cur_str = game_tpl;
							cur_str = cur_str.replace('{{GAME_ID}}', game);
							cur_str = cur_str.replace('{{GAME_ID}}', game);
							game_str += cur_str;
						});
						game_view.html(game_str);
						var games = game_view.find('[data-gameid]');
						$.each(games, function(g_id) {
							var game = games.eq(g_id);
							game.off('click');
							game.on('click', self.game_clicked(monopoly, game.data('gameid')));
						});
					}
				});

			}
		};
		_.delay(df, 1000);
		df();
		console.log("HOP HOP");
	};
	self.uninitialize = function(monopoly, parent_span) {
		self.is_active = false;
	};
	self.game_clicked = function(monopoly, game_id) {
		return function() {
			monopoly.game_id = game_id;
			monopoly.set_state('JoinGameState');
		};
	};
	return self;
};

function CreateGameState() {
	var self = this;
	StateBase(self);
	self.title = 'Create a new game';
	self.initialize = function(monopoly, parent_span) {
		monopoly.send_request({game:null}, function(data, err) {
			if(err) {
				console.log(err);
				monopoly.set_state('InitialState');
			} else if(data.success == false) {
				console.log(data);
				monopoly.set_state('InitialState');
			} else {
				monopoly.game_id = data.game;
				monopoly.set_state('JoinGameState');
			}
		});
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function JoinGameState() {
	var self = this;
	StateBase(self);
	self.title = 'Join game';
	self.initialize = function(monopoly, parent_span) {
		parent_span.find('[data-gamename]').html(monopoly.game_id);
		parent_span.find('[data-joingame]').off();
		parent_span.find('[data-joingame]').on('click', function(event) {
			event.preventDefault();
			var name = parent_span.find('[data-username]').val()
			monopoly.send_event('add_player', [name], function(data, err) {
				if(err) {
					console.log(err);
					monopoly.set_state('InitialState');
				} else if(data.success == false) {
					console.log(data);
					monopoly.set_state('InitialState');
				} else {
					monopoly.set_state('WaitForPlayersState');
				}
			});
		});
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function WaitForPlayersState() {
	var self = this;
	StateBase(self);
	self.title = 'Waiting for players...';
	self.initialize = function(monopoly, parent_span) {
		self.is_active = true;
		var df = function() {
			if(self.is_active) {
				_.delay(df, 1000);
				monopoly.send_request({game:monopoly.game_id, get_players:true}, function(resp, err) {
					if(err) {
						console.log(err);
						monopoly.set_state('InitialState');
					} else if(resp.success == false) {
						console.log(resp);
						monopoly.set_state('InitialState');
					} else {
						var player_view = parent_span.find('[data-currentplayers]');
						var player_str = '';
						_.each(resp.players, function(player) {
							player_str += player + ", "
						});
						player_view.html(player_str);
					}
				});

			}
		};
		_.delay(df, 1000);
		df();
	};
	self.uninitialize = function(monopoly, parent_span) {
		self.is_active = false;
	};
	return self;
};
function BeforeStartGameState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
		monopoly.send_event('start_game', [], function(data, err) {
			if(err) {
				console.log(err);
				monopoly.set_state('InitialState');
			} else if(data.success == false) {
				console.log(data);
				monopoly.set_state('InitialState');
			} else {
				monopoly.start_game(data);
			}
		});
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};
function StartingState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function PlayerTurnState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
		monopoly.send_event('detect_state', []);
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function NotInJailState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};
function BuyPropertyPromptState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};
function OpenCardPromptState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function IncomeTaxPromptState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

function GameOverState() {
	var self = this;
	StateBase(self);
	self.initialize = function(monopoly, parent_span) {
	};
	self.uninitialize = function(monopoly, parent_span) {
	};
	return self;
};

monopoly = new function() {
	var self = this;
	// self.states = []
	// self.states.push(InitialState);
	self.cur_state = null;
	self.game_id = null;
	self.player_name = '';
	self.game_started = false;
	self.last_msg = {};
	self.start_game = function(data) {
		self.game_started = true;
		self.handle_msg(data)
	};
	self.handle_msg = function(data) {
		self.last_msg = data;
		var state_name = data.new_state_str.toCamel();
		console.log("Detected state to be " + state_name);
		self.set_state(state_name + 'State');
	};
	self.first_run = function() {
	};
	self.send_request = function(data, cb) {
		if(self.game_started) {
			$.ajax({
				url: '/monopoly/cors/',
				data: JSON.stringify(data),
				type: 'POST',
				contentType: "application/json",
				crossDomain: true,
				dataType: 'json',
				success: function(data) { self.handle_msg(data) },
				error: function(data) { console.log(data) },
			});
		} else {
			$.ajax({
				url: '/monopoly/cors/',
				data: JSON.stringify(data),
				type: 'POST',
				contentType: "application/json",
				crossDomain: true,
				dataType: 'json',
				success: function(data) { cb(data); },
				error: function(data) { cb(null, data) },
			});
		}
	};
	self.send_event = function(event, params, cb) {
		var req = {game:self.game_id, event:event, params:params};
		self.send_request(req, cb);
	}
	self.set_state = function(new_state_name) {
		console.log("Setting state to " + new_state_name);
		var new_state_class = window[new_state_name];
		var parent_span = $('[data-gamestate=' + new_state_name + ']');
		$('[data-gamestate]').addClass('hidden');
		if(self.cur_state) {
			self.cur_state.base.uninitialize(self, parent_span);
			self.cur_state.uninitialize(self, parent_span);
		}
		parent_span.removeClass('hidden');
		self.cur_state = new new_state_class();
		self.cur_state.base.initialize(self, parent_span);
		self.cur_state.initialize(self, parent_span);
		$('title').html(self.cur_state.title);
	};
	self.first_run();
	// self.game_id = 0;
	// self.set_state('JoinGameState');
	self.set_state('InitialState');
	return self;
};
