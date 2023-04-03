import socket
import threading

MANAGER_HOST = '127.0.0.1'
MANAGER_PORT = 50000

class Peer:
	def __init__(self, manager_address):
		self.manager_host,self.manager_port = manager_address
		# Socket for communication with manager
		self.manager = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Socket for incoming connections
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.bind(('', 0))
		self.host, self.port = self.socket.getsockname()

	def handleManager(self):
		while True:
			data = self.manager.recv(1024)
			if not data:
				raise Exception('Manager disconnected!')
			
			if data == b'PING':
				print('[INFO] Pong!')
				self.manager.sendall(b'PONG')
				continue
			
			print('[INFO] Received peer update!')
			self.peers = [(p.split(",")[0], p.split(",")[1]) for p in data.decode().split(';')]
			print(self.peers)

	def run(self):
		try:
			self.manager.connect((self.manager_host, self.manager_port))
			self.manager.sendall(f"{self.host},{self.port}".encode())
			self.handleManager()

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

if __name__ == '__main__':
	Peer((MANAGER_HOST, MANAGER_PORT)).run()