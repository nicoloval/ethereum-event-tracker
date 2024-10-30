import subprocess
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('.env')

# Load environment variables
RPC_ENDPOINT = os.getenv('RPC_ENDPOINT')
ABI = os.getenv('ABI')
OUTPUT = os.getenv('OUTPUT')
EVENT = os.getenv('EVENT')

# Establish a Web3 connection
w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT, request_kwargs={'timeout': 40}))
print(f'Chain connected?: {w3.is_connected()}')

# Define the block range size
BLOCK_RANGE_SIZE = 500000

# Get the latest block number
latest_block = w3.eth.block_number

# Function to run event_tracker.py for a given block range
def run_event_tracker(from_block, to_block):
    subprocess.run([
        'python', 'event_tracker.py',
        '-n', 'stETH',  # Example contract name
        '-a', '0x1234567890abcdef1234567890abcdef12345678',  # Example contract address
        '-e', 'Transfer',  # Example event name
        '-f', str(from_block),
        '-r', str(to_block),
        '-p'
    ])

# Launch subprocesses for each block range
processes = []
for start_block in range(0, latest_block, BLOCK_RANGE_SIZE):
    end_block = min(start_block + BLOCK_RANGE_SIZE, latest_block)
    process = subprocess.Popen([
        'python', 'event_tracker.py',
        '-n', 'stETH',  # Example contract name
        '-a', '0x1234567890abcdef1234567890abcdef12345678',  # Example contract address
        '-e', 'Transfer',  # Example event name
        '-f', str(start_block),
        '-r', str(end_block),
        '-p'
    ])
    processes.append(process)

# Wait for all processes to complete
for process in processes:
    process.wait()

print("All event tracking processes have completed.")
