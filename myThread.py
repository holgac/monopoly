import threading
import sys
import time

class myClientThread(threading.Thread):

    def __init__(self, connection, client_address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.client_address = client_address
        self.size = 1024

    def acceptedConnection(self):
        try:
            print >>sys.stderr, 'connection from', self.client_address

            # Receive the data in small chunks and retransmit it
            while True:
                data = self.connection.recv(self.size)
                print >>sys.stderr, 'received "%s"' % data
                if data:
                    print >>sys.stderr, 'sending data back to the client'
                    self.connection.sendall(data)
                else:
                    print >>sys.stderr, 'no more data from', self.client_address
                    break

        finally:
            # Clean up the connection
            self.connection.close()

    def run(self):
        print "my thread ", id(threading.current_thread), " is started"
        self.acceptedConnection()
        time.sleep(2)
        print "my thread ", id(threading.current_thread), " is running"
        time.sleep(2)
        print "my thread ", id(threading.current_thread), " is stopped"
