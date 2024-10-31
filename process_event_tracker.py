"""This script connects to an Ethereum node and
finds all the occurrences of a specific event, saving them to a single file.
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
        # Configure the paths to the files from user information
        self.contract_abi_path = f"{ABI}/{self.contract_name}.json"
        self.event_solidity_path = f"{EVENT}/{self.contract_name}-{self.event_name}.sol"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Event Tracker Configuration")
    parser.add_argument('-n', '--contract-name', type=str, required=True, help='Contract name')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-name', type=str, required=True, help='Event name')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-r', '--recent-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')

    args = parser.parse_args()
    
    return EventTrackerConfig(
        args.contract_name,
        args.contract_address,
        args.event_name,
        args.from_block,
        args.recent_block,
        args.append
    )

REQ_SIZE = 10000
ABI = os.getenv('ABI')
OUTPUT = os.getenv('OUTPUT')
EVENT = os.getenv('EVENT')

config = parse_arguments()

w3 = Web3(
    Web3.HTTPProvider(
        os.getenv('RPC_ENDPOINT'),
        request_kwargs={'timeout': 40}
    )
)
print(f'Chain connected?: {w3.is_connected()}')

def get_logs_try(w3, filter_params):
    logs = w3.eth.get_logs(filter_params)
    return logs

if config.from_block is None:
    fromblock = 0
else:
    fromblock = config.from_block

if config.recent_block is None:
    recent_block = w3.eth.block_number
else:
    recent_block = config.recent_block

f = open(config.contract_abi_path)
contract_abi = json.load(f)
contract = w3.eth.contract(address=config.contract_address, abi=contract_abi)
event_abi_map = log_decoder.generate_event_abi_map(contract_abi)

event = parse_solidity_event(config.event_solidity_path)

# output = pd.DataFrame(columns=['blockNumber'] + event['fields'])

output_file = f"{OUTPUT}/{config.contract_name}-{config.event_name}-{fromblock}-{recent_block}.parquet"

if config.append and os.path.exists(output_file):
    existing_table = pq.read_table(output_file)
    existing_df = existing_table.to_pandas()
    last_block_number = existing_df['blockNumber'].astype(int).max()
    fromblock = last_block_number + 1
    logger.info(f'Appending to existing file {output_file}, starting from block {fromblock}')
else:
    logger.info(f'Creating new output file {output_file}')

# list to save all output dicts
output_list = []

for step in np.arange(fromblock, recent_block, REQ_SIZE):
    toblock = min(step + REQ_SIZE, recent_block)
    args = {
        'fromBlock': step,
        'toBlock': toblock,
        'address': config.contract_address,
        'topics': ['0x' + Web3.keccak(text=event['event_name'] + '(' + ",".join(event['types']) + ')').hex()]
    }
    filter_params = log_filters.make_filter(args)

    logs = get_logs_try(w3, filter_params)

    if len(logs) > 0:
        logger.info(f'found {len(logs)} events. Processing...')

        for log in logs:
            decoded_log = log_decoder.decode_log(log, event_abi_map, contract)
            work = {'blockNumber': decoded_log['blockNumber']}
            for field in event['fields']:
                work[field] = decoded_log['args'][field]
            
            output_list.append(work)

    # output dataframe out of the list of events stored as dicts
    output = pd.DataFrame(output_list)
    # Write the DataFrame to the output file at the end
    if os.path.exists(output_file):
        existing_table = pq.read_table(output_file)
        existing_df = existing_table.to_pandas()
        output = pd.concat([existing_df, output], ignore_index=True)

    # Convert columns to string to avoid errors from numbers larger than max
    output = output.astype(str)
    table = pa.Table.from_pandas(output)
    pq.write_table(table, output_file)
    logger.info(f'Final output written to {output_file}')

logger.info(f'Event Tracker job finished.')
