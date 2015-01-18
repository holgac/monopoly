from django.shortcuts import render
from django.http import HttpResponse
import json, socket, traceback

# Create your views here.

def index(request):
	return render(request, 'index.html', {})

def cors(request):
	bdy = json.loads(request.body)
	port = 3001
	server_address = ('huseyinolgac.com', port)
	connected = False
	print 'connecting to',port
	while not connected:
		print 'connecting to',port
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			server_address = ('huseyinolgac.com', port)
			sock.connect(server_address)
			print 'connected to',port
			connected = True
		except:
			sock.close();
			traceback.print_exc()
			port += 1
			if port > 3005:
				print 'probably server is down..'
				return HttpResponse({'success':False, 'message':"server is down"})
	sock.sendall(json.dumps(bdy))
	resp = sock.recv(65536)
	return HttpResponse(resp)
