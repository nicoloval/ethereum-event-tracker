"""This script connects to an Ethereum node and
finds all the occurrences of a specific event, saving them to a single file.
It is meant to run as a process cmd managed by the script parallel_event_tracker.py
"""
import argparse
from web3 import Web3
import os
import pandas as pd
import json
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from logger import setup_logging, logging
from log_decoder import generate_event_abi_map, decode_log
from log_filters import make_filter
from parse_solidity_event import parse_solidity_event

# TK optimal 10000, alchemy is 2k
REQ_SIZE = 2000

class EventTrackerConfig:
    def __init__(self, contract_file, contract_address, event_file, from_block, to_block, append, log_file, output_file, rpc):
        self.output_file = output_file
        self.contract_abi_path = contract_file
        self.contract_address = contract_address
        self.event_solidity_path = event_file
        self.from_block = from_block
        self.to_block = to_block
        self.append = append
        self.log_file_path = log_file
        self.rpc = rpc
        
def parse_arguments():
    parser = argparse.ArgumentParser(description="Event Tracker Configuration")
    parser.add_argument('-n', '--contract-file', type=str, required=True, help='Contract ABI file path')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-file', type=str, required=True, help='Event file path')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-t', '--to-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')
    parser.add_argument('-l', '--log-file', type=str, required=True, help='Path to the log file')
    parser.add_argument('-o', '--output-file', type=str, required=True, help='Output file path')
    parser.add_argument('-r', "--rpc", type=str, required=True, help="the rpc connection")

    args = parser.parse_args()
    
    return EventTrackerConfig(
        args.contract_file,
        args.contract_address,
        args.event_file,
        args.from_block,
        args.to_block,
        args.append,
        args.log_file,
        args.output_file,
        args.rpc
    )

def main():
    config = parse_arguments()

    # Set up logging
    setup_logging(log_file_path=config.log_file_path)
    logger = logging.getLogger()
    logger.info(f"Started event tracking with arguments: contract_file={config.contract_abi_path}, contract_address={config.contract_address}, event_file={config.event_solidity_path}, from_block={config.from_block}, to_block={config.to_block}, append={config.append}, log_file={config.log_file_path}, output_file={config.output_file}, rpc={config.rpc}")

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
        fromblock = config.from_block

    if config.to_block is None:
        to_block = w3.eth.block_number
    else:
        to_block = config.to_block

    f = open(config.contract_abi_path)
    contract_abi = json.load(f)
    contract = w3.eth.contract(address=config.contract_address, abi=contract_abi)
    event_abi_map = generate_event_abi_map(contract_abi)

    event = parse_solidity_event(config.event_solidity_path)

    # output = pd.DataFrame(columns=['blockNumber'] + event['fields'])
    # if the file already exists and it is append mode
    # don't repeat the analysis
    if config.append and os.path.exists(config.output_file):
        existing_table = pq.read_table(config.output_file)
        existing_df = existing_table.to_pandas()
        last_block_number = existing_df['blockNumber'].astype(int).max()
        fromblock = last_block_number + 1
        del existing_df

    # list to save all output dicts
    output_list = []

    print('fromblock', fromblock)
    print('toblock', to_block)
    print('reqsize', REQ_SIZE)

    for step in np.arange(fromblock, to_block, REQ_SIZE):
        toblock = min(step + REQ_SIZE, to_block)
        args = {
            'fromBlock': step,
            'toBlock': toblock,
            'address': config.contract_address,
            'topics': ['0x' + Web3.keccak(text=event['event_name'] + '(' + ",".join(event['types']) + ')').hex()]
        }
        filter_params = make_filter(args)

        logs = get_logs_try(w3, filter_params)

        if len(logs) > 0:

            for log in logs:
                decoded_log = decode_log(log, event_abi_map, contract)
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
    ##### write the output
    # if the file already exists just append to the existing
    if config.append and os.path.exists(config.output_file):
        existing_table = pq.read_table(config.output_file)
        existing_df = existing_table.to_pandas()
        output = pd.concat([existing_df, output], ignore_index=True)
    
    # Convert columns to string to avoid errors from numbers larger than max
    for c in event['fields']:
        output[c] = output[c].astype(str)
    output['blockNumber'] = output['blockNumber'].astype(int)
    table = pa.Table.from_pandas(output)
    pq.write_table(table, config.output_file)
    logger.info(f"Dumped logs to file {config.output_file}")

if __name__ == "__main__":
    main()
