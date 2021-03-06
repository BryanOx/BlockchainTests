# LIBS
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# BLOCKCHAIN

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while not check_proof:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]

            if block['previous_hash'] != self.hash(previous_block):
                return False

            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()).hexdigest()

            if hash_operation[:4] != '0000':
                return False

            previous_block = block
            block_index += 1

        return True

    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({
            'Sender': sender,
            'Reciever': reciever,
            'Amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index']+1

    def add_node(self, address):
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)
        print(self.nodes)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

    # def get_coins(self, address):
    #     balance = 0
    #     for block in self.chain:
    #         if len(block['transactions']) > 0:
    #             for t in block['transactions']:
    #                 if t['Reciever'] == address:
    #                     balance += t['Amount']
    #     return balance


# INICIAR FLASK
app = Flask(__name__)


# CREANDO UNA DIR PARA EL NODO EL EL PUERTO 5001
node_address = str(uuid4()).replace('-', '')

blockchain = Blockchain()

# MINAR PRIMER BLOQUE

@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof=previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, reciever='8a613964c300459ca7d9be5df9fee432', amount=50)
    block = blockchain.create_block(proof=proof, previous_hash=previous_hash)
    response = {
        'message': 'Felicidades, has minado un bloque!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


# OBTENER TODA LA CADENA

@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


# CHECK VALIDEZ DE BLOCKCHAIN
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {
            'message': 'Todo perfecto, blockchain valido'
        }
    else:
        response = {
            'message': 'El blockchain es invalido'
        }
    return jsonify(response), 200


# AGREGANDO NUEVA TRANSACCION AL BLOCKCHAIN
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Algun elemento de la transaccion esta faltando', 401
    index = blockchain.add_transaction(
        json['sender'], json['receiver'], json['amount'])
    response = {
        'message': f'La transaccion sera a??adida al bloque {index}'
    }
    return jsonify(response), 201


# PASO 3 - DECENTRALIZANDO EL BLOCKCHAIN

# CONECTANDO NUEVOS NODOS
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get("nodes")
    if nodes is None:
        return 'No node', 401
    for node in nodes:
        blockchain.add_node(node)
    response = {
        'message': 'Todos los nodos estan conectados.',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201


# REEMPLAZANDO CADENA POR LA MAS LARGA
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'Los nodos tenian diferentes cadenas, entonces la cadena fue reemplazada por la mas larga',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Todo bien. La cadena es la mas larga',
            'actual_chain': blockchain.chain
        }
    return jsonify(response), 200

# @app.route('/get_coins', methods=['POST'])
# def get_coins():
#     json = request.get_json()
#     address = json['Address']
#     coins = blockchain.get_coins(address=address)
#     response = {
#         'message':'Address encontrada y con este balance de katcoins',
#         'Address':address,
#         'Balance':coins
#     }
#     return jsonify(response), 201

# CORRER APP DE FLASK PARA MINAR
app.run(host='0.0.0.0', port='5001')
