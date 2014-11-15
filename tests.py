import json, httplib, re, datetime, sys, time
import unittest
import monopoly

class CreationTests(unittest.TestCase):
	verbose = True
	def setUp(self):
		self.start_time = time.time()
	def tearDown(self):
		t = time.time() - self.start_time
		t = float(str(t))
		t = float(int(t*1000)/1000.0)
		sys.stdout.write(' time: ' + str(t) + '  status: ')
		sys.stdout.flush()
	def test_creation(self):
		m = monopoly.Monopoly()
		self.assertTrue(m.state == monopoly.Monopoly.GameState.uninitialized)
		player_names = ['Mal', 'Zoe', 'Wash', 'Inara', 'Jayne',
			'Kaylee', 'Simon', 'River', 'Shepherd']
		e = monopoly.StartGameEvent(player_names)
		r = m.handle_event(e)
		self.assertTrue(r.event == e)
		self.assertTrue(r.success == True)
		self.assertTrue(r.response == None)
		roll_success = False
		while not roll_success:
			e = monopoly.RollDieForTheFirstTimeEvent()
			r = m.handle_event(e)
			self.assertTrue(r.event == e)
			roll_success = r.success
		for p in player_names:
			self.assertTrue(p in r.response)

if __name__ == '__main__':
	import os
	try:
		os.remove('resp.html')
	except Exception, e:
		pass
	loader = unittest.TestLoader()
	ln = lambda f: getattr(AllTests, f).im_func.func_code.co_firstlineno
	lncmp = lambda a, b: cmp(ln(a), ln(b))
	loader.sortTestMethodsUsing = lncmp
	unittest.main(testLoader=loader, verbosity=2)
