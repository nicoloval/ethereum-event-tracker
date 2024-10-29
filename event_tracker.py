"""This script connects to an Ethereum node and
find all the occurences of a specific event.
"""
from config import *
import argparse
from web3 import Web3
import logger, logging, os
import log_decoder
import log_filters
from dotenv import load_dotenv
import pandas as pd
import json
import numpy as np
from parse_solidity_event import parse_solidity_event
from tqdm import tqdm
import sys

logger.setup_logging()
logger = logging.getLogger()

load_dotenv('.env')

class EventTrackerConfig:
    def __init__(self, contract_name, contract_address, event_name, from_block, recent_block, append):
        self.contract_name = contract_name
        self.contract_address = contract_address
        self.event_name = event_name
        self.from_block = from_block
        self.recent_block = recent_block
        self.append = append
        # Configure the paths to the files form user information
        self.contract_abi_path = f"./{ABI}/{self.contract_name}.json"
        self.event_solidity_path = f"./{EVENT}/{self.contract_name}-{self.event_name}.sol"
        self.output_path = f"./{OUTPUT}/{self.contract_name}-{self.event_name}.csv"


import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Event Tracker Configuration")
    parser.add_argument('-n', '--contract-name', type=str, required=True, help='Contract name')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-name', type=str, required=True, help='Event name')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-r', '--recent-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')

    args = parser.parse_args()
    
    # Assuming EventTrackerConfig is a class you've defined elsewhere
    return EventTrackerConfig(
        args.contract_name,
        args.contract_address,
        args.event_name,
        args.from_block,
        args.recent_block,
        args.append  # Passes the boolean as required
    )


# TK opptimally set
REQ_SIZE=10000

# Parse arguments
config = parse_arguments()

# establish w3 conn
w3 = Web3(
    Web3.HTTPProvider(
        os.getenv('RPC_ENDPOINT'),
        request_kwargs={'timeout': 40}
        )
        )
print(f'Chain connected?: {w3.is_connected()}')

# @log_filters.retry_on_error(max_retries=MAX_TRIES, delay=TIME_DELAY)
def get_logs_try(w3,filter_params):
    logs = w3.eth.get_logs(filter_params)
    return logs

# last block on abacus-1: 18012051
# set blocks range to examine
if config.from_block is None:
    fromblock = 0
else:
    fromblock = config.from_block

if config.recent_block is None:
    recent_block = w3.eth.block_number
else:
    recent_block = config.recent_block

# prep log decoding 
f = open(config.contract_abi_path)
contract_abi = json.load(f)
contract = w3.eth.contract(address=config.contract_address, abi=contract_abi)
event_abi_map = log_decoder.generate_event_abi_map(contract_abi)

# event .sol information parsing
event = parse_solidity_event(config.event_solidity_path)

# Initialize an empty DataFrame to store the event occurences
output = pd.DataFrame(columns=['blockNumber'] + event['fields'])

# initialize output csv
if not os.path.exists(f'{config.output_path}'):
    os.makedirs(f'{OUTPUT}', exist_ok=True)
    logger.info(f'No previous output file exists')
else:
    if config.append:
        logger.info(f'Appending to previous existing output')   
        history = pd.read_csv(f'{config.output_path}')
        fromblock = history.iloc[-1]['blockNumber']+1        
    else:
        output.to_csv(config.output_path, index=False, mode='w', header=True)
        logger.info(f'Overwriting previous exisiting output')


# DEBUG: this Transfer happened
# blockNumber                                         18006108
# from              0xadce54380e5b5f62eab82a34ce27f904e4172af3
# to                0x889edc2edab5f40e902b864ad4d7ade8e412f9b1
# fromIsContract                                             0
# toIsContract                                               1
# value  
# # setting for the debug                                   420004762656680918
# fromblock    = 18006105
# recent_block = 18006110

for ii, step in enumerate(tqdm(np.arange(fromblock, recent_block, REQ_SIZE), desc="Processing blocks")):

    toblock = min(step + REQ_SIZE, recent_block)
    #get logs
    args = {}
    args['fromBlock'] = step 
    args['toBlock'] = toblock 
    # the contract address
    args['address'] = config.contract_address
    # the event to track
    str2kek = event['event_name'] + '(' + ",".join(event['types']) + ')'
    # the 0x depends on the web3 version
    args['topics'] = ['0x'+ Web3.keccak(text=str2kek).hex()]
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
            for field in event['fields']:
                work[field] = decoded_log['args'][field]

            # Append the work dictionary as a new row to the DataFrame
            success_row = pd.DataFrame([work])
            output = pd.concat([output, success_row], ignore_index=True)

    # Save the DataFrame to a CSV file
    output.to_csv(config.output_path, index=False, mode='a', header=not os.path.exists(config.output_path))

logger.info(f'Event Tracker job finished.')
