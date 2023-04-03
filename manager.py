import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 50000

class Manager:
	class Peer:
		def __init__(self, internal, external):
			self.conn, self.addr = internal
			self.host, self.port = external

	def __init__(self, host, port, timeout=60):
		# Setup socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((host, port))

		self.timeout = timeout
		self.lock = threading.Lock()
		self.active_peers = []

	def broadcastActivePeers(self):
		self.lock.acquire()
		for peer in self.active_peers:
			l = ';'.join([f"{p.host},{p.port}" for p in self.active_peers if p != peer])
			peer.conn.sendall(l.encode())
		self.lock.release()

	def registerPeer(self, peer):
		peer.conn.settimeout(self.timeout)
		self.lock.acquire()
		if peer not in self.active_peers:
			print(f'[INFO] New peer connected: {peer.addr}')
			self.active_peers.append(peer)
		self.lock.release()

		self.broadcastActivePeers()

	def unregisterPeer(self, peer):
		self.lock.acquire()
		if peer in self.active_peers:
			print(f'[INFO] Peer disconnected: {peer.addr}')
			self.active_peers.remove(peer)
		self.lock.release()
		peer.conn.close()

		self.broadcastActivePeers()

	def handlePeer(self, peer):
		while True:
			try:
				data = peer.conn.recv(1024)

				if not data or data == b'CLOSE':
					self.unregisterPeer(peer)
					break
			except socket.timeout:
				print(f'[INFO] Pinging {peer.addr}')
				peer.conn.sendall(b'PING')
				data = peer.conn.recv(1024)
				if not data == b'PONG':
					self.unregisterPeer(peer)
					break
					

	def handleConnections(self):
			while True:
				self.socket.listen()
				conn, addr = self.socket.accept()
				host, port = conn.recv(1024).decode().split(',')

				self.registerPeer(self.Peer((conn, addr), (host, int(port))))

				threading.Thread(target=self.handlePeer, args=(self.active_peers[-1],), daemon=True).start()

	def run(self):
		print('[NOTICE] Manager started!')

		try:
			self.handleConnections()
		except KeyboardInterrupt:
			print('[NOTICE] Shutting down...')
			self.socket.close()
			for peer in self.active_peers.copy():
				peer.conn.close()
				self.active_peers.remove(peer)
			exit(0)
		except Exception as e:
			self.socket.close()
			for peer in self.active_peers.copy():
				peer.conn.close()
				self.active_peers.remove(peer)
			print(f'[ERROR] {e}')
			raise

if __name__ == '__main__':
	Manager(HOST, PORT).run()