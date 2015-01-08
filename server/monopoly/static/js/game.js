function StateBase(state) {
	var self = this;
	state.base = this;
	state.title = 'DUMMY TITLE';
	return self;
};

function InitialState() {
	var self = this;
	StateBase(self);
	self.title = 'Welcome to Monopoly!';
	self.initialize = function(monopoly, parent_span) {
		var buttons = parent_span.find('[data-newstate]');
		$.each(buttons, function(buttonIdx) {
			// button.off('click');
			var button = buttons.eq(buttonIdx);
			button.on('click', function(event) {
				monopoly.set_state(button.data('newstate'));
			});
		});
	};
	self.uninitialize = function(monopoly, parent_span) {
		var buttons = parent_span.find('[data-newstate]');
		$.each(buttons, function(button) {
			button.off('click');
		});
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
			var data = {};
			data.game = monopoly.game_id;
			data.event = 'add_player';
			data.params = [name];
			monopoly.send_request(data, function(data, err) {
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
			}
		};
		_.delay(df, 1000);
		df();
		console.log("HOP HOP");
	};
	self.uninitialize = function(monopoly, parent_span) {
		self.is_active = false;
	};
	return self;
};

monopoly = new function() {
	var self = this;
	// self.states = []
	// self.states.push(InitialState);
	self.cur_state = null;
	self.game_id = null;
	self.first_run = function() {
	};
	self.send_request = function(data, cb) {
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
	};
	self.set_state = function(new_state_name) {
		var new_state_class = window[new_state_name];
		var parent_span = $('[data-gamestate=' + new_state_class.name + ']');
		$('[data-gamestate]').addClass('hidden');
		if(self.cur_state) {
			self.cur_state.uninitialize(self, parent_span);
		}
		parent_span.removeClass('hidden');
		self.cur_state = new_state_class();
		self.cur_state.initialize(self, parent_span);
		$('title').html(self.cur_state.title);
	};
	self.first_run();
	// self.game_id = 0;
	// self.set_state('JoinGameState');
	self.set_state('InitialState');
	return self;
};
