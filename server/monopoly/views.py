from django.shortcuts import render
from django.http import HttpResponse
import json, socket

# Create your views here.

def index(request):
	return render(request, 'index.html', {})

def cors(request):
	bdy = json.loads(request.body)
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	port = 3001
	server_address = ('huseyinolgac.com', port)
	connected = False
	while not connected:
		try:
			print 'connecting to',port
			server_address = ('huseyinolgac.com', port)
			sock.connect(server_address)
			print 'connected to',port
			connected = True
		except:
			port += 1
	sock.sendall(json.dumps(bdy))
	resp = sock.recv(65536)
	sock.close();
	return HttpResponse(resp)
