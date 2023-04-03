import os
import socket
import threading

MANAGER_HOST = '127.0.0.1'
MANAGER_PORT = 50000

class Peer:
	def __init__(self, manager_address, verbose=False):
		self.verbose = verbose
		self.manager_host,self.manager_port = manager_address

		# Setup shared folder
		self.folder = input('Path to shared folder (i.e. contains files that can be shared): ')
		try:
			if not os.path.isdir(self.folder):
				raise Exception('Could not find folder! Make sure the path is relative or absolute.')
		except Exception as e:
			print(f'[ERROR] {e}')
			exit(1)
		
		# Socket for incoming requests
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(('', 0))
		self.host, self.port = self.socket.getsockname()

		# Socket for communication with manager
		self.manager = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.manager.connect((self.manager_host, self.manager_port))
		self.manager.sendall(f"{self.host},{self.port}".encode())

	def handleManager(self):
		# Handle pings and peer updates from manager
		while True:
			data = self.manager.recv(1024)
			if not data:
				raise Exception('Manager disconnected!')
			
			if data == b'PING':
				if self.verbose: print('[INFO] Pong!')
				self.manager.sendall(b'PONG')
				continue
			
			if self.verbose: print('[INFO] Received peer update!')
			self.peers = [(p.split(",")[0], int(p.split(",")[1])) for p in data.decode().split(';')]

	def handleRequests(self):
			# Handle incoming requests from other peers
			while True:
				self.socket.listen()
				conn, addr = self.socket.accept()
				request = conn.recv(1024).decode()

				if self.verbose: print(f'[INFO] New request from {addr} for {request}')

				if request in os.listdir(self.folder):
					length = os.path.getsize(os.path.join(self.folder, request))
					conn.sendall(str(length).encode())
				else:
					conn.sendall(b'SORRY')

				conn.close()

	def findHosts(self, filename):
		# Find hosts that have the requested file
		hosts = []
		for peer in self.peers:
			conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			conn.connect(peer)
			conn.sendall(filename.encode())
			data = conn.recv(1024)
			if data == b'SORRY':
				continue
			hosts.append(peer)
			conn.close()
		return hosts

	def run(self):
		try:
			threading.Thread(target=self.handleManager, daemon=True).start()
			threading.Thread(target=self.handleRequests, daemon=True).start()
			while True:
				# Wait for peers to be available
				if not hasattr(self, 'peers') or len(self.peers) == 0:
					print('[NOTICE] Waiting for peers to be available...')
					while not hasattr(self, 'peers'):
						pass
				# Choose file to request
				filename = input('Filename of the file to request: ')
				if filename in os.listdir(self.folder):
					print('[ERROR] You already have this file!')
					continue
				# Find hosts that have the requested file
				hosts = self.findHosts(filename)
				print(hosts)

		except KeyboardInterrupt:
			self.manager.sendall(b'CLOSE')
			self.manager.close()
			print('[NOTICE] Shutting down...')
			exit(0)

		except Exception as e:
			self.manager.sendall(b'CLOSE')
			self.manager.close()
			print(f'[ERROR] {e}')
			raise
			exit(1)

if __name__ == '__main__':
	Peer((MANAGER_HOST, MANAGER_PORT), True).run()