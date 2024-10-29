"""This script connects to an Ethereum node and
find all the occurences of a specific event.
"""
from config import *
from web3 import Web3
import logger, logging, os
import log_decoder
import log_filters
from dotenv import load_dotenv
import pandas as pd
import uuid
import json
import numpy as np
import hashlib

logger.setup_logging()
logger = logging.getLogger()

load_dotenv('.env')

# global vars
REQ_SIZE=10000

# establish w3 conn
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_ENDPOINT'),request_kwargs={'timeout': 40}))
print(f'Chain connected?: {w3.is_connected()}')

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


# normal setting
recent_block = w3.eth.block_number
# last block on abacus-1: 18012051

# prep log decoding 
contract_abi_path =  './contracts/stETH-abi.json'
f = open(contract_abi_path)
contract_abi = json.load(f)
contract = w3.eth.contract(address=os.getenv('stETH_address'), abi=contract_abi)
event_abi_map = log_decoder.generate_event_abi_map(contract_abi)

# initialize output csv
output_path = './output/stETH_Transfer.csv' 
if not os.path.exists(f'{history_path}'):
    os.makedirs('./output', exist_ok=True)
    logger.info(f'no previous output file exists')
    fromblock = 11000000
    history=pd.DataFrame()
else:
    logger.info(f'output file exists')
    history = pd.read_csv(f'{history_path}')
    fromblock = history.iloc[-1]['blockNumber']+1

# Initialize an empty DataFrame to store the logs
output = pd.DataFrame(columns=['blockNumber', 'from', 'to', 'value'])

# DEBUG: this Transfer happened
# blockNumber                                         18006108
# from              0xadce54380e5b5f62eab82a34ce27f904e4172af3
# to                0x889edc2edab5f40e902b864ad4d7ade8e412f9b1
# fromIsContract                                             0
# toIsContract                                               1
# value  
# # setting for the debug                                   420004762656680918
# fromblock = 18006105
# recent_block = 18006110
for ii, step in enumerate(np.arange(fromblock, recent_block, REQ_SIZE)):

    toblock = min(step + REQ_SIZE, recent_block)
    #get logs
    args = {}
    args['fromBlock'] = step 
    args['toBlock'] = toblock 
    # the contract address
    args['address'] = stETH_address
    # the Transfer event to track
    # the 0x depends on the web3 version
    args['topics'] = ['0x'+ Web3.keccak(text='Transfer(address,address,uint256)').hex()]
    filter_params = log_filters.make_filter(args)

    # fetching logs
    logs = get_logs_try(w3, filter_params)

    if(len(logs)>0):
        logger.info(f'found {len(logs)} events. Processing...')

        # process each log      
        for log in logs:
            decoded_log = log_decoder.decode_log(log, event_abi_map, contract)
            # generate nonce as an identifier
            work={}
            work['blockNumber']=decoded_log['blockNumber']
            work['from']=decoded_log['args']['from']
            work['to']=decoded_log['args']['to']
            work['value'] = decoded_log['args']['value']  # in wei

            # Append the work dictionary as a new row to the DataFrame
            success_row = pd.DataFrame([work])
            output = pd.concat([output, success_row], ignore_index=True)

    # Save the DataFrame to a CSV file
    output.to_csv(output_path, index=False, mode='a', header=not os.path.exists(output_path))

logger.info(f'Event Tracker job finished.')
