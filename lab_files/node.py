from argparse import ArgumentParser
import json
from threading import Lock
import socketserver
import socket

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
			try:
				json_data = json.loads(data)
				if json_data['type'] == "transaction":
					with self.server.blockchain.print_lock:
						print("[NET] Received a transaction from node {}: {}".format(self.client_address[0], json_data['payload']))

					with self.server.blockchain_lock:
						added = self.server.blockchain.add_transaction(json.dumps(json_data['payload']))	
						print("this is response sent: {}".format(json.dumps({'response': added})))
						send_prefixed(self.request, json.dumps({'response': added}).encode())

				elif json_data['type'] == "values":
					#send blocks with corresponding indexes
					# less than len get them from chain
					# greater than or equal to propose a new block with index of that
					with self.server.blockchain.print_lock:
						print("[BLOCK] Received a block request from node {}: {}".format(self.client_address[0], json_data['payload']))

					if json_data['payload'] < len(self.server.blockchain.blockchain):
						response = json.dumps([self.server.blockchain.blockchain[json_data['payload']]])

					else:
						if self.server.start_consensus == False:
							my_block = self.server.blockchain.propose_block(self.server.blockchain.last_block()['current_hash'])
							# check if block proposed is same as index wanted
							if my_block['index'] == json_data['payload']:
								self.server.blockchain.proposed_blocks.append(my_block)
							self.server.start_consensus = True

						with self.server.blockchain_lock:
							# look through transactions that have index of 2
							response = json.dumps(self.server.blockchain.proposed_blocks)
							
					with self.server.blockchain_lock:
						send_prefixed(self.request, response.encode())
			except TypeError:
				continue

class Node():
    def __init__(self, host: str, port: int, sending_socket: socket.socket):
        self.host = host
        self.port = port
        self.sending_socket = sending_socket