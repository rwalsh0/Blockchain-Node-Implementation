import lab_files.network as network
from lab_files.node import MyTCPServer
import lab_files.blockchain as blockchain

import sys
import socket
import socketserver
import threading
import time

import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519


class Node():
    def __init__(self, host: str, port: int, sending_socket: socket.socket):
        self.host = host
        self.port = port
        self.sending_socket = sending_socket

nodes: list[Node] = []
consensus_started = 0

def main():
    samp_transaction_request = {
        "type": "transaction", 
        "payload": {
            "sender": "a57819938feb51bb3f923496c9dacde3e9f667b214a0fb1653b6bfc0f185363b",
            "message": "hello",
            "nonce": 0,
            "signature": "142e395895e0bf4e4a3a7c3aabf2f59d80c517d24bb2d98a1a24384bc7cb29c9d593ce3063c5dd4f12ae9393f3345174485c052d0f5e87c082f286fd60c7fd0c"
        }
    }

    samp_transaction_response = {
        "response": True
    }


    samp_block_request = {"type": "values", "payload": 2}

    samp_block_response = [
        {
            "index": 2,
            "transactions":[
                {"sender": "a57819938feb51bb3f923496c9dacde3e9f667b214a0fb1653b6bfc0f185363b",
                 "message": "hello",
                 "nonce": 0,
                 "signature": "142e395895e0bf4e4a3a7c3aabf2f59d80c517d24bb2d98a1a24384bc7cb29c9d593ce3063c5dd4f12ae9393f3345174485c052d0f5e87c082f286fd60c7fd0c"
                }
            ],
            "previous_hash": "03525042c7132a2ec3db14b7aa1db816e61f1311199ae2a31f3ad1c4312047d1",
            "current_hash": "5c0ada1107f87eee93b675cc9e7d772424013add94e202a8d578a16298c30c19"
        }
    ]

    #get port server
    #get nodes
    server_port = int(sys.argv[1])
    node_config = sys.argv[2]
    # TODO: check input validity??

    node_config = open(node_config,"r")
    nodes_raw = node_config.readlines()
    for raw in nodes_raw:
        addr = raw.split(":")
        nodes.append(Node(addr[0], int(addr[1]), None))
    
    connect_neighbours()
    
    HOST = 'localhost'

    with MyTCPServer((HOST, server_port)) as server:
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

    print(server.blockchain.last_block())

    try:
        while True:
            continue
    except KeyboardInterrupt:
        exit()



def client():
    #make transaction
    private_key = ed25519.Ed25519PrivateKey.generate()
    sender = private_key.public_key().public_bytes_raw().hex()
    message = 'hello'
    signature = blockchain.make_signature(private_key, message)
    transaction = blockchain.make_transaction(sender, message, signature)

    #send transaction
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 8000))

    network.send_prefixed(s, transaction.encode())
    try:
        data = network.recv_prefixed(s).decode()
        print(data)
    except Exception as e:
        print(e)


#connects to neighbours and adds them to the list of connections
def connect_neighbours():
    # Connect to all clients that are trying to connect. 
    # This runs in parallel with the main function to catch all clients wanting to connect at any time
    for node in nodes:
        thread_conn_node = threading.Thread(target=connect_to_node, args=[node], daemon=True)
        thread_conn_node.start()

def connect_to_node(node: Node):
    sending_socket = socket.socket()
    while True:
        if consensus_started == True:
            sending_socket.settimeout(5)
        try:
            sending_socket.connect((node.host,node.port))
            node.sending_socket = sending_socket
            print(f"received connection from node {(node.host,node.port)}")
            return
        except ConnectionRefusedError:
            continue
        except TimeoutError:
            break


if __name__ == "__main__":
    main()

