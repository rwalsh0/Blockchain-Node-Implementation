from cryptography.exceptions import InvalidSignature
import cryptography.hazmat.primitives.asymmetric.ed25519 as ed25519
from enum import Enum
import hashlib
import json
import re
from threading import Lock

sender_valid = re.compile('^[a-fA-F0-9]{64}$')
signature_valid = re.compile('^[a-fA-F0-9]{128}$')

TransactionValidationError = Enum('TransactionValidationError', ['INVALID_JSON', 'INVALID_SENDER', 'INVALID_MESSAGE', 'INVALID_SIGNATURE'])

def make_transaction(sender, message, nonce, signature) -> str:
	return json.dumps({'sender': sender, 'message': message, 'nonce': nonce, 'signature': signature})

def transaction_bytes(transaction: dict) -> bytes:
	return json.dumps({k: transaction.get(k) for k in ['sender', 'message']}, sort_keys=True).encode()

def make_signature(private_key: ed25519.Ed25519PrivateKey, message: str) -> str:
	transaction = {'sender': private_key.public_key().public_bytes_raw().hex(), 'message': message}
	return private_key.sign(transaction_bytes(transaction)).hex()

def validate_transaction(transaction: str) -> dict | TransactionValidationError:
	try:
		tx = json.loads(transaction)
	except json.JSONDecodeError:
		return TransactionValidationError.INVALID_JSON

	if not(tx.get('sender') and isinstance(tx['sender'], str) and sender_valid.search(tx['sender'])):
		return TransactionValidationError.INVALID_SENDER

	if not(tx.get('message') and isinstance(tx['message'], str) and len(tx['message']) <= 70 and tx['message'].isalnum()):
		return TransactionValidationError.INVALID_MESSAGE

	public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx['sender']))
	if not(tx.get('signature') and isinstance(tx['signature'], str) and signature_valid.search(tx['signature'])):
		return TransactionValidationError.INVALID_SIGNATURE
	try:
		public_key.verify(bytes.fromhex(tx['signature']), transaction_bytes(tx))
	except InvalidSignature:
		return TransactionValidationError.INVALID_SIGNATURE

	return tx


class Blockchain():
	def  __init__(self):
		self.blockchain = []
		self.pool = []
		self.proposed_blocks = []
		# sender, num_of_transactions
		self.senders = []
		self.print_lock = Lock()
		self.new_block(self.propose_block('0' * 64))


	def new_block(self, block=None):
		with self.print_lock:
			print("[CONSENSUS] Appended to the blockchain: {}".format(block['current_hash']))
		self.blockchain.append(block)
		self.proposed_blocks = []

	def propose_block(self, previous_hash=None):
		block = {
			'index': len(self.blockchain),
			'transactions': self.pool.copy(),
			'previous_hash': previous_hash or self.blockchain[-1]['current_hash'],
		}
		block['current_hash'] = self.calculate_hash(block)
		with self.print_lock:
			print("[PROPOSAL] Created a block proposal: {}".format(block))
		self.pool = []
		return block

	def last_block(self):
		return self.blockchain[-1]

	def calculate_hash(self, block: dict) -> str:
		block_object: str = json.dumps({k: block.get(k) for k in ['index', 'transactions', 'previous_hash']}, sort_keys=True)
		block_string = block_object.encode()
		raw_hash = hashlib.sha256(block_string)
		hex_hash = raw_hash.hexdigest()
		return hex_hash

	def add_transaction(self, transaction: str) -> bool:
		try:
			tx = validate_transaction(transaction)
			if isinstance(tx, dict):
				# check same sender and same nonce is not in pool together
				sender_added = False
				for idx, sender in enumerate(self.senders):
					if tx['sender'] == sender[0]:
						sender_added = True
						# if greater than update new nonce
						if tx['nonce'] > sender[1]:
							self.senders[idx][1] = tx['nonce']	
						# if equal to or less than return invalid nonce
						else:
							with self.print_lock:
								print("[TX] Received an invalid transaction, wrong sender - {}".format(transaction))
							return False
						
				self.pool.append(tx)
				if not sender_added:
					self.senders.append([tx['sender'], tx['nonce']])
				with self.print_lock:
					print("[MEM] Stored transaction in the transaction pool: {}".format(tx['signature']))
				return True
			
			elif tx == TransactionValidationError.INVALID_SENDER:
				with self.print_lock:
					print("[TX] Received an invalid transaction, wrong sender - {}".format(transaction))
			elif tx == TransactionValidationError.INVALID_MESSAGE:
				with self.print_lock:
					print("[TX] Received an invalid transaction, wrong message - {}".format(transaction))
			elif tx == TransactionValidationError.INVALID_SIGNATURE:
				with self.print_lock:
					print("[TX] Received an invalid transaction, wrong signature - {}".format(transaction))
		except KeyError:
			pass

		return False
