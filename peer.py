import os
import socket
import threading

MANAGER_HOST = '127.0.0.1'
MANAGER_PORT = 50000

class Peer:
	def __init__(self, manager_address, verbose=False, chunk_size=1000):
		self.verbose = verbose
		self.chunk_size = chunk_size
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

				if request.split(' ')[0] == 'GET':
					filename = request.split(' ')[1]
					chunk = int(request.split(' ')[2])
					if self.verbose: print(f'[INFO] New request from {addr} for {filename} chunk {chunk}')

					if filename in os.listdir(self.folder):
						with open(os.path.join(self.folder, filename), 'rb') as f:
							f.seek(chunk * self.chunk_size)
							data = f.read(self.chunk_size)
						conn.sendall(data)

					conn.close()

				else:
					if self.verbose: print(f'[INFO] New request from {addr} for {request}')

					if request in os.listdir(self.folder):
						length = os.path.getsize(os.path.join(self.folder, request))
						conn.sendall(str(length).encode())
					else:
						conn.sendall(b'SORRY')

					conn.close()

	def findHosts(self, filename):
		# Find hosts that have the requested file
		length = None
		hosts = []
		for peer in self.peers:
			conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			conn.connect(peer)
			conn.sendall(filename.encode())
			data = conn.recv(1024)
			if data == b'SORRY':
				continue
			if not length:
				length = int(data.decode())
			elif length != int(data.decode()):
				raise Exception('File length mismatch!')
			hosts.append(peer)
			conn.close()
		return hosts, length
	
	def getChunk(self, host, filename, chunk):
		# Get a chunk from a host
		conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		conn.connect(host)
		conn.sendall(f"GET {filename} {chunk}".encode())
		data = conn.recv(1024)
		if not data:
			raise Exception('Peer disconnected!')
		conn.close()
		return data

	def transferFromPeer(self, host, filename, num_chunks, reqs, req_lock, data, data_lock):
		# Run transfer from peer
		while True:
			with data_lock:
				if len(data) == num_chunks:
					break

			with req_lock:
				if not reqs:
					continue
				req = reqs.pop()

			try:
				chunk = self.getChunk(host, filename, req)
				with data_lock:
					data[req] = chunk
			except:
				with req_lock:
					reqs.append(req)
				break

	def getFile(self, filename):
		# Find hosts that have the requested file
		hosts, length = self.findHosts(filename)
		
		num_chunks = -(length // -self.chunk_size)
		reqs = list(range(num_chunks))
		req_lock = threading.Lock()
		data = {}
		data_lock = threading.Lock()
		
		# Start threads to transfer from each host
		threads = []
		for host in hosts:
			threads.append(threading.Thread(target=self.transferFromPeer, args=(host, filename, num_chunks, reqs, req_lock, data, data_lock), daemon=True))
			threads[-1].start()
		
		# Wait for threads to finish
		for thread in threads:
			thread.join()

		print('[INFO] Merge chunks...')
	
		# file_data = b''
		# for i in range(len(data)):
		# 	file_data += data[i]
		file_data = b''.join([data[i] for i in range(len(data))])

		with open(os.path.join(self.folder, filename), 'wb') as f:
			f.write(file_data)

		print('[INFO] File transfer complete!')

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
				
				# Request file
				self.getFile(filename)

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
	Peer((MANAGER_HOST, MANAGER_PORT, True)).run()