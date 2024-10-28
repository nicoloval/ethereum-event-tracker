"""This script connects to an Ethereum node and
find all the occurences of a specific event.
"""
from config import *
from web3 import Web3
import logger, logging, os
import log_decoder
from dotenv import load_dotenv
import pandas as pd
import uuid

logger.setup_logging()
logger = logging.getLogger()

load_dotenv('.env')

# global vars
REQ_SIZE=10000

# establish w3 conn
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_ENDPOINT'),request_kwargs={'timeout': 40}))
print(f'Chain connected?: {w3.is_connected()}')

# get history csv
history_path = './history/history.csv' 
if not os.path.exists(f'{history_path}'):
    os.makedirs('./history', exist_ok=True)
    logger.info(f'no previous history file exists')
    fromblock = 6654121
    history=pd.DataFrame()
else:
    logger.info(f'history file exists')
    history = pd.read_csv(f'{history_path}')
    fromblock = history.iloc[-1]['blockNumber']+1

# some functions 
# @log_filters.retry_on_error(max_retries=MAX_TRIES, delay=TIME_DELAY)
def get_logs_try(w3,filter_params):
    logs = w3.eth.get_logs(filter_params)
    return logs
    

def generate_hash_nonce():
    # Generate a random UUID first
    unique_data = uuid.uuid4().hex
    
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256(unique_data.encode())
    
    # Return the hex digest of the hash
    nonce = hash_object.hexdigest()
    return nonce[:64]  # Truncate to fit 32 bytes since Solidity bytes32 type is 32 bytes long

# listen to event 
# get recent block
recent_block = w3.eth.block_number

# prep log decoding 
contract_abi =  '../contracts/stETH-abi.json'
contract = w3.eth.contract(address=os.getenv('stETH_address'), abi=contract_abi)
event_abi_map = log_decoder.generate_event_abi_map(contract_abi)


