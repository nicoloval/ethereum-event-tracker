"""This script connects to an Ethereum node and
finds all the occurrences of a specific event, saving them to a single file.
It is meant to run as a process cmd managed by the script parallel_event_tracker.py
"""
import argparse
from web3 import Web3
import os
from logger import setup_logging, logging
import log_decoder
import log_filters
from dotenv import load_dotenv
import pandas as pd
import json
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from parse_solidity_event import parse_solidity_event

load_dotenv('.env')

class EventTrackerConfig:
    def __init__(self, contract_name, contract_address, event_name, from_block, to_block, append, log_file, output):
        self.output = output
        self.contract_name = contract_name
        self.contract_address = contract_address
        self.event_name = event_name
        self.from_block = from_block
        self.to_block = to_block
        self.append = append
        self.log_file_path = log_file
        # Configure the paths to the files from user information
        self.contract_abi_path = f"{ABI}/{self.contract_name}.json"
        self.event_solidity_path = f"{EVENT}/{self.contract_name}-{self.event_name}.sol"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Event Tracker Configuration")
    parser.add_argument('-n', '--contract-name', type=str, required=True, help='Contract name')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-name', type=str, required=True, help='Event name')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-t', '--to-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')
    parser.add_argument('-l', '--log-file', type=str, required=True, help='Path to the log file')
    parser.add_argument('-o', '--output', type=str, help='Output file path (optional)')

    args = parser.parse_args()
    
    return EventTrackerConfig(
        args.contract_name,
        args.contract_address,
        args.event_name,
        args.from_block,
        args.to_block,
        args.append,
        args.log_file,
        args.output
    )

# TK optimal 10000, alchemy is 2k
REQ_SIZE = 2000
ABI = os.getenv('ABI')
OUTPUT = os.getenv('OUTPUT')
EVENT = os.getenv('EVENT')

config = parse_arguments()

# Set up logging
setup_logging(log_file_path=config.log_file_path)
logger = logging.getLogger()
logger.info(f"Started event tracking for contract: {config.contract_name}, event: {config.event_name}, address: {config.contract_address}, block range: {config.from_block} to {config.to_block}")

w3 = Web3(
    Web3.HTTPProvider(
        os.getenv('RPC_ENDPOINT'),
        request_kwargs={'timeout': 40}
    )
)
logger.info(f'Chain connected?: {w3.is_connected()}')

def get_logs_try(w3, filter_params):
    try:
        logs = w3.eth.get_logs(filter_params)
        logger.info(f"Retrieved {len(logs)} logs from block {filter_params['fromBlock']} to {filter_params['toBlock']}")
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        logs = []
    return logs

if config.from_block is None:
    fromblock = 0
else:
    pass
    fromblock = config.from_block

if config.to_block is None:
    to_block = w3.eth.block_number
else:
    to_block = config.to_block

f = open(config.contract_abi_path)
contract_abi = json.load(f)
contract = w3.eth.contract(address=config.contract_address, abi=contract_abi)
event_abi_map = log_decoder.generate_event_abi_map(contract_abi)

event = parse_solidity_event(config.event_solidity_path)

# output = pd.DataFrame(columns=['blockNumber'] + event['fields'])

output_file = config.output if config.output else f"{OUTPUT}/{config.contract_name}-{config.event_name}-{fromblock}-{to_block}.parquet"

if config.append and os.path.exists(output_file):
    existing_table = pq.read_table(output_file)
    existing_df = existing_table.to_pandas()
    last_block_number = existing_df['blockNumber'].astype(int).max()
    fromblock = last_block_number + 1
    del existing_df

# list to save all output dicts
output_list = []

for step in np.arange(fromblock, to_block, REQ_SIZE):
    toblock = min(step + REQ_SIZE, to_block)
    args = {
        'fromBlock': step,
        'toBlock': toblock,
        'address': config.contract_address,
        'topics': ['0x' + Web3.keccak(text=event['event_name'] + '(' + ",".join(event['types']) + ')').hex()]
    }
    filter_params = log_filters.make_filter(args)

    logs = get_logs_try(w3, filter_params)

    if len(logs) > 0:

        for log in logs:
            decoded_log = log_decoder.decode_log(log, event_abi_map, contract)
            work = {
                'blockNumber': decoded_log['blockNumber'],
                'transactionHash': decoded_log['transactionHash']
                }
            for field in event['fields']:
                work[field] = decoded_log['args'][field]
            
            output_list.append(work)

logger.info(f"Finished processing logs for address: {config.contract_address}, block range: {config.from_block} to {config.to_block}. Total events found: {len(output_list)}")

# create the columns, so that if output_list is empty the dataframe has the right header
columns = ['blockNumber', 'transactionHash'] + event['fields']
logger.info(f"Output Dataframe columns: {columns}")
# output dataframe out of the list of events stored as dicts
output = pd.DataFrame(output_list, columns=columns)
# Write the DataFrame to the output file at the end
if os.path.exists(output_file):
    existing_table = pq.read_table(output_file)
    existing_df = existing_table.to_pandas()
    output = pd.concat([existing_df, output], ignore_index=True)

# Convert columns to string to avoid errors from numbers larger than max
for c in event['fields']:
    output[c] = output[c].astype(str)
output['blockNumber'] = output['blockNumber'].astype(int)
table = pa.Table.from_pandas(output)
pq.write_table(table, output_file)
logger.info(f"Dumped logs to file {output_file}")
