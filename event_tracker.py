"""This script connects to an Ethereum node and
find all the occurences of a specific event.
"""
from config import *
from web3 import Web3
import logger, logging

# global vars
REQ_SIZE=10000

# establish w3 conn
w3_pow = Web3(Web3.HTTPProvider(os.getenv('POW_RPC_ENDPOINT')))
w3_pos = Web3(Web3.HTTPProvider(os.getenv('POS_RPC_ENDPOINT')))
print(f'PoW chain connected?: {w3_pow.is_connected()}')
print(f'PoS chain connected?: {w3_pos.is_connected()}')
