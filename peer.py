import socket
import threading

HOST = '127.0.0.1'
PORT = 50000

class Peer:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def handleManager(self):
		while True:
			data = self.socket.recv(1024)
			if not data:
				raise Exception('Manager disconnected!')
			
			if data == b'PING':
				print('[INFO] Pong!')
				self.socket.sendall(b'PONG')
				continue
			
			print('[INFO] Received peer update!')
			self.peers = [(p.split(",")[0], p.split(",")[1]) for p in data.decode().split(';')]

	def run(self):
		try:
			self.socket.connect((self.host, self.port))
			self.handleManager()

		except KeyboardInterrupt:
			self.socket.sendall(b'CLOSE')
			self.socket.close()
			print('[NOTICE] Shutting down...')
			exit(0)

		except Exception as e:
			self.socket.sendall(b'CLOSE')
			self.socket.close()
			print(f'[ERROR] {e}')
			raise

if __name__ == '__main__':
	Peer(HOST, PORT).run()