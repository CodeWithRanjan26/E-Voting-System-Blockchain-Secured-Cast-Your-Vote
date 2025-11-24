from hashlib import sha256
import json
import time
from flask import Blueprint, request, jsonify

# Blueprint for blockchain service
service = Blueprint("service", __name__)

# ================================
# BLOCK + BLOCKCHAIN IMPLEMENTATION
# ================================
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith("0" * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return block_hash.startswith("0" * Blockchain.difficulty) and block_hash == block.compute_hash()

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions.copy(),
            timestamp=time.time(),
            previous_hash=last_block.hash,
        )

        proof = Blockchain.proof_of_work(new_block)
        added = self.add_block(new_block, proof)

        if added:
            self.unconfirmed_transactions = []
            return new_block.index

        return False


# Initialize blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

peers = set()

# ================================
# API ROUTES (Blueprint)
# ================================

@service.route("/new_transaction", methods=["POST"])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["voter_id", "party"]

    # Validate fields
    for field in required_fields:
        if not tx_data.get(field):
            return jsonify({"error": "Missing field: " + field}), 400

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)

    return jsonify({"message": "Transaction added"}), 201


@service.route("/chain", methods=["GET"])
def get_chain():
    chain_data = []

    for block in blockchain.chain:
        block_data = block.__dict__.copy()
        chain_data.append(block_data)

    return jsonify({
        "length": len(chain_data),
        "chain": chain_data,
        "peers": list(peers)
    })


@service.route("/mine", methods=["GET"])
def mine_block():
    result = blockchain.mine()

    if not result:
        return jsonify({"message": "No transactions to mine"}), 404

    return jsonify({
        "message": f"Block #{result} mined successfully"
    }), 200


@service.route("/pending_tx", methods=["GET"])
def get_pending_tx():
    return jsonify(blockchain.unconfirmed_transactions), 200
