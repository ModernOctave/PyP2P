import socket
import threading
from time import time

HOST = '127.0.0.1'
PORT = 50000

class Manager:
	class Peer:
		def __init__(self, conn, addr):
			self.conn = conn
			self.addr = addr

	def __init__(self, host, port):
		# Setup socket
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((host, port))
		self.socket.settimeout(60)

		self.active_peers = []

		print('[NOTICE] Manager started!')

	def broadcastActivePeers(self):
		for peer in self.active_peers:
			peer.conn.sendall(';'.join([f"{p.addr[0]},{p.addr[1]}" for p in self.active_peers]).encode())

	def registerPeer(self, peer):
		self.active_peers.append(peer)
		print(f'[INFO] New peer connected: {peer.addr}')

		self.broadcastActivePeers()

	def unregisterPeer(self, peer):
		self.active_peers.remove(peer)
		peer.conn.close()
		print(f'[INFO] Peer disconnected: {peer.addr}')

		self.broadcastActivePeers()

	def handlePeer(self, peer):
		lastContacted = time()
		while True:
			data = peer.conn.recv(1024)
			if not data or data == b'CLOSE':
				self.unregisterPeer(peer)
				break

			if time() - lastContacted > 60:
				peer.conn.sendall(b'PING')
				data = peer.conn.recv(1024)
				if not data == b'PONG':
					# Peer disconnected
					self.unregisterPeer(peer)
					break

	def run(self):
		try:
			while True:
				self.socket.listen()
				conn, addr = self.socket.accept()

				self.active_peers.append(self.Peer(conn, addr))
				print(f'[INFO] New peer connected: {addr}')

				self.broadcastActivePeers()

				threading.Thread(target=self.handlePeer, args=(self.active_peers[-1],)).start()

		except KeyboardInterrupt:
			self.socket.close()
			print('[NOTICE] Shutting down...')
			exit(0)

		except Exception as e:
			self.socket.close()
			print('[ERROR] Something went wrong!')
			print(e)
			exit(1)

if __name__ == '__main__':
	Manager(HOST, PORT).run()