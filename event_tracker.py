"""This script connects to an Ethereum node and
find all the occurences of a specific event.
"""
import argparse
from web3 import Web3
import logger, logging, os
import log_decoder
import log_filters
from dotenv import load_dotenv
import pandas as pd
import json
import pyarrow as pa
import pyarrow.parquet as pq
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
        self.contract_abi_path = f"{ABI}/{self.contract_name}.json"
        self.event_solidity_path = f"{EVENT}/{self.contract_name}-{self.event_name}.sol"


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
# load path variables
ABI = os.getenv('ABI')
OUTPUT = os.getenv('OUTPUT')
EVENT = os.getenv('EVENT')

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

# Initialize an empty DataFrame to store the event occurrences
output = pd.DataFrame(columns=['blockNumber'] + event['fields'])

# Check existing files to determine the starting block if append is True
if config.append:
    existing_files = [f for f in os.listdir(OUTPUT) if f.startswith(f"{config.contract_name}-{config.event_name}")]
    if existing_files:
        latest_file = max(existing_files, key=lambda x: int(x.split('-')[-2]))
        fromblock = int(latest_file.split('-')[-1].split('.')[0]) + 1
        logger.info(f'Resuming from block {fromblock} based on existing files.')
    else:
        logger.info(f'No previous output file exists, starting from block {fromblock}')
else:
    if os.path.exists(OUTPUT):
        logger.info(f'Overwriting previous existing output')
    else:
        os.makedirs(OUTPUT, exist_ok=True)


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

output_list = []
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
            output_list.append(work)
            
            # output = pd.concat([output, success_row], ignore_index=True)

    output = pd.DataFrame(output_list)
    # Determine the current output file based on the current 500,000 block range
    current_file_start = (step // 500000) * 500000
    current_file_end = min(current_file_start + 500000, recent_block)
    output_file = f"{OUTPUT}/{config.contract_name}-{config.event_name}-{current_file_start}-{current_file_end}.parquet"

    # Append the DataFrame to the current parquet file every REQ_SIZE steps
    if os.path.exists(output_file):
        existing_table = pq.read_table(output_file)
        existing_df = existing_table.to_pandas()
        output = pd.concat([existing_df, output], ignore_index=True)

    # Convert columns to string to avoid errors from numbers larger than max
    output = output.astype(str)
    table = pa.Table.from_pandas(output)
    pq.write_table(table, output_file)
    logger.info(f'Updated output in {output_file}')

    # Reset the DataFrame every 500,000 blocks
    if (step + REQ_SIZE) % 500000 == 0:
        output = pd.DataFrame(columns=['blockNumber'] + event['fields'])  # Reset the DataFrame

logger.info(f'Event Tracker job finished.')
