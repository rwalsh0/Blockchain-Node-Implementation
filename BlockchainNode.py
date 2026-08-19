import lab_files.network as network
import lab_files.node as node
import lab_files.blockchain as blockchain

import sys
import socket
import socketserver
import threading
import time
import math
import json

from argparse import ArgumentParser

import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519

# TODO: more transaction checking
#get port server
#get nodes
parser = ArgumentParser()
parser.add_argument('port', type=int)
parser.add_argument('config', type=str)
args = parser.parse_args()
port: int = args.port
config: int = args.config
# TODO: check input validity??

HOST = 'localhost'
server = node.MyTCPServer((HOST, port), node.MyTCPHandler)


def main():
    global server

    # receive transactions / fill pool
    try:
        while True:
            try:
                while True:
                    # transaction pool becomes non-empty
                    with server.blockchain_lock:
                        try:
                            if len(server.blockchain.pool) != 0:
                                break
                        # the node receives a request from another node asking for the value of the next round
                        
                            if server.start_consensus == True:
                                break
                        except KeyboardInterrupt:
                            exit()

                # propose block

                # consensus logic
                # each loop send block requests and append all proposed blocks to list of proposed blocks
                #check index in every block is the same
                server.nodes, decided_block = consensus_protocol(server.nodes, math.ceil(len(server.nodes)/2))

                # keep track of senders and their nonces
                # done for transactions?
                with server.blockchain_lock:
                    if decided_block:
                        server.blockchain.new_block(decided_block)                

                server.start_consensus = False
            except KeyboardInterrupt:
                exit()

    except KeyboardInterrupt:
        exit()


def consensus_protocol(nodes: list[node.Node], f: int=2):
    assert(len(nodes) >= f)

    responses_count = [0] * len(nodes)
    block_request = {
        'type': "values",
        'payload': len(server.blockchain.blockchain)
    }
    for _ in range(f + 1):
        #might have to thread the loop below
        # USE LOCK on 

        for idx, node in enumerate(nodes):
            # get block proposals from all nodes
            # send block request
            try:
                if node.sending_socket:
                    network.send_prefixed(node.sending_socket, json.dumps(block_request).encode())
                else:
                    continue
                # receive block response (wait 5 seconds and catch exception with one more try)
                #node.sending_socket.settimeout(5)

                block_response = json.loads(network.recv_prefixed(node.sending_socket).decode())
                # append blocks

                if block_response:
                    for block in block_response:
                        if block not in server.blockchain.proposed_blocks:
                            server.blockchain.proposed_blocks.append(block)
                    responses_count[idx] += 1

            except ConnectionResetError or TimeoutError:
                try:
                    node.sending_socket.settimeout(None)
                    node.sending_socket.connect((node.host, node.port))
                except OSError:
                    nodes.pop(idx)

            # if they have a hash for the corresponding index append to known hashes
            # get all blocks with same index and add to blocks
    can_decide = responses_count.count(f + 1) >= len(nodes) - f
    if not can_decide:
        print("didnt decide")
    # decided block:
    #   > 1 transaction
    #   lowest lexicographical representation of current hash
    decided_block = None
    for block in server.blockchain.proposed_blocks:
        if len(block['transactions']) > 0:
            if decided_block == None:
                decided_block = block
            elif block['current_hash'] < decided_block['current_hash']:
                decided_block = block

    for node in nodes:
        if node.sending_socket:
            node.sending_socket.settimeout(None)

    return nodes, decided_block if can_decide else None


def connect_to_node(index: int):
    global server

    nod = server.nodes[index]

    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        if server.start_consensus == True:
            sending_socket.settimeout(5)
        try:
            sending_socket.connect((server.nodes[index].host,server.nodes[index].port))
            server.nodes[index].sending_socket = sending_socket
            #print(f"received connection from node {(server.nodes[index].host,server.nodes[index].port)}")
            return
        except KeyboardInterrupt:
            exit()
        except ConnectionRefusedError:
            continue

        except TimeoutError:
            try:
                sending_socket.settimeout(None)
                sending_socket.connect((server.nodes[index].host,server.nodes[index].port))
            except ConnectionRefusedError:
                server.nodes.pop(index)


if __name__ == "__main__":
    node_config = open(config,"r")
    nodes_raw = node_config.readlines()
    for raw in nodes_raw:
        addr = raw.split(":")
        server.nodes.append(node.Node(addr[0], int(addr[1]), None))

    threading.Thread(target=main, daemon=True).start()

    for idx, n in enumerate(server.nodes):
        threading.Thread(target=connect_to_node, args=[idx], daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        exit()
