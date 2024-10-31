import subprocess
import os
from web3 import Web3
import argparse
from dotenv import load_dotenv
from logger import setup_logging, logging

setup_logging()
logger = logging.getLogger()

load_dotenv('.env')

# Load environment variables
RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')
ABI = os.getenv('ABI')
OUTPUT = os.getenv('OUTPUT')
EVENT = os.getenv('EVENT')

# Establish a Web3 connection
w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT, request_kwargs={'timeout': 40}))
logger.info(f'Chain connected?: {w3.is_connected()}')

# Define the block range size
BLOCK_RANGE_SIZE = 500000

# Get the latest block number
latest_block = w3.eth.block_number

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parallel Event Tracker Configuration")
    parser.add_argument('-n', '--contract-name', type=str, required=True, help='Contract name')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-name', type=str, required=True, help='Event name')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-r', '--recent-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')
    parser.add_argument('-c', '--cores', type=int, default=4, help='Number of cores to allocate to subprocesses (optional)')

    return parser.parse_args()

args = parse_arguments()
logger.info(f"Arguments received: contract_name={args.contract_name}, contract_address={args.contract_address}, event_name={args.event_name}, from_block={args.from_block}, recent_block={args.recent_block}, append={args.append}, cores={args.cores}")

# Determine the starting and ending blocks
start_block = args.from_block if args.from_block is not None else 0
end_block = args.recent_block if args.recent_block is not None else latest_block

# Adjust the first batch if start_block is not a multiple of BLOCK_RANGE_SIZE
first_batch_end = ((start_block // BLOCK_RANGE_SIZE) + 1) * BLOCK_RANGE_SIZE if start_block % BLOCK_RANGE_SIZE != 0 else start_block + BLOCK_RANGE_SIZE

# Launch subprocesses for each block range
processes = []
for current_start_block in range(start_block, end_block, BLOCK_RANGE_SIZE):
    if current_start_block == start_block and start_block % BLOCK_RANGE_SIZE != 0:
        current_end_block = min(first_batch_end, end_block)
    else:
        current_end_block = min(current_start_block + BLOCK_RANGE_SIZE, end_block)
    current_end_block = min(current_start_block + BLOCK_RANGE_SIZE, end_block)
    cmd = [
        'python', 'process_event_tracker.py',
        '-n', args.contract_name,
        '-a', args.contract_address,
        '-e', args.event_name,
        '-f', str(current_start_block),
        '-r', str(current_end_block)
    ]

    if args.append:
        cmd.append('-p')

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    processes.append(process)

# Wait for all processes to complete, respecting the core limit
while processes:
    for process in processes:
        if process.poll() is not None:  # Process has finished
            processes.remove(process)
            break
    if len(processes) >= args.cores:
        processes[0].wait()  # Wait for the first process to finish if core limit is reached

logger.info("All event tracking processes have completed.")
