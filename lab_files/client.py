import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
import socket
import json
import random

from blockchain import Blockchain, make_signature, make_transaction
from network import recv_prefixed, send_prefixed

private_key = ed25519.Ed25519PrivateKey.generate()
sender = private_key.public_key().public_bytes_raw().hex()
message = 'hello'
nonce = 1
signature = make_signature(private_key, message)
transaction = make_transaction(sender, message, nonce, signature)

blockchain = Blockchain()

transaction_request = {
	'type': "transaction",
	'payload': json.loads(transaction)
}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('localhost', 5001))

send_prefixed(s, json.dumps(transaction_request).encode())

try:
	data = recv_prefixed(s).decode()
	print(data)
except Exception as e:
	print(e)