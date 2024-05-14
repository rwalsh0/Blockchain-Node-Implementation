from argparse import ArgumentParser
import json
from threading import Lock
import socketserver
import socket

#from blockchain import Blockchain
#from network import recv_prefixed, send_prefixed
from lab_files.blockchain import Blockchain
from lab_files.network import recv_prefixed, send_prefixed

class MyTCPServer(socketserver.ThreadingTCPServer):
	def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
		self.blockchain = Blockchain()
		self.blockchain_lock = Lock()
		self.nodes :list[Node] = []
		self.start_consensus = False
		super().__init__(server_address, RequestHandlerClass, bind_and_activate)

class MyTCPHandler(socketserver.BaseRequestHandler):
	server: MyTCPServer

	def handle(self):
		while True:
			try:
				data = recv_prefixed(self.request).decode()
			except:
				break
			json_data = json.loads(data)
			if json_data['type'] == "transaction":
				print("[NET] Received a transaction from node {}: {}".format(self.client_address[0], json_data['payload']))

				with self.server.blockchain_lock:
					added = self.server.blockchain.add_transaction(json.dumps(json_data['payload']))	
					send_prefixed(self.request, json.dumps({'response': added}).encode())

			elif json_data['type'] == "values":
				print("[BLOCK] Received a block request from node {}: {}".format(self.client_address[0], json_data['payload']))
				if self.server.start_consensus == False and json_data['payload'] > len(self.server.blockchain.blockchain):
					self.server.blockchain.propose_block(self.server.blockchain.last_block()['current_hash'])
					self.server.start_consensus = True

				with self.server.blockchain_lock:
					# look through transactions that have index of 2
					print(f" this is the props blocks : {self.server.blockchain.proposed_blocks}")
					request = json.dumps(self.server.blockchain.proposed_blocks)
					print(f"this was sent back {request}")
					send_prefixed(self.request, request.encode())

class Node():
    def __init__(self, host: str, port: int, sending_socket: socket.socket):
        self.host = host
        self.port = port
        self.sending_socket = sending_socket

if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('port', type=int)
	args = parser.parse_args()
	port: int = args.port

	HOST = 'localhost'

	with MyTCPServer((HOST, port), MyTCPHandler) as server:
		server.serve_forever()
