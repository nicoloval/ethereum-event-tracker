import subprocess
import os
import os
from web3 import Web3
from tqdm import tqdm
import argparse
from logger import setup_logging, logging
import time
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parallel Event Tracker Configuration")
    parser.add_argument('-n', '--contract-file', type=str, required=True, help='Contract ABI file path')
    parser.add_argument('-a', '--contract-address', type=str, required=True, help='Contract address')
    parser.add_argument('-e', '--event-file', type=str, required=True, help='Event file path')
    parser.add_argument('-f', '--from-block', type=int, default=None, help='Starting block number (optional)')
    parser.add_argument('-t', '--to-block', type=int, default=None, help='Stopping block number (optional)')
    parser.add_argument('-p', '--append', action="store_true", help='Append to existing output (optional)')
    parser.add_argument('-c', '--cores', type=int, default=4, help='Number of cores to allocate to subprocesses (optional)')
    parser.add_argument('-r', "--rpc", type=str, required=True, help="the rpc connection")
    parser.add_argument('-l', '--log-dir', type=str, default=None, help='Path to the log file')
    parser.add_argument('-o', '--output-dir', type=str, required=True, help='The directory where to store the output')
    parser.add_argument('-x', '--output-prefix', type=str, default=None, help='the prefix the output files will use')

    return parser.parse_args()

def main():   
    # Determine the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    args = parse_arguments()
    # set up log
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    if args.log_dir == None:
        log_dir = f'./logs/{current_time}'
    else:
        log_dir = args.log_dir
    log_path = f'{log_dir}/job_main.log'
    setup_logging(log_file_path=log_path)
    logger = logging.getLogger()
    # check whether output dir exists

    # Define the block range size
    BLOCK_RANGE_SIZE = 500000

    # Establish a Web3 connection
    w3 = Web3(Web3.HTTPProvider(args.rpc, request_kwargs={'timeout': 40}))
    logger.info(f'Chain connected?: {w3.is_connected()}')
    # Get the latest block number
    latest_block = w3.eth.block_number

    logger.info(f"Arguments received: contract_file={args.contract_file}, contract_address={args.contract_address}, event_file={args.event_file}, from_block={args.from_block}, to_block={args.to_block}, append={args.append}, cores={args.cores}, rpc={args.rpc}, log_dir={args.log_dir}, output_dir={args.output_dir}, output_prefix={args.output_prefix}")

    # Determine the starting and ending blocks
    start_block = args.from_block if args.from_block is not None else 0
    end_block = args.to_block if args.to_block is not None else latest_block

    # Adjust the first batch if start_block is not a multiple of BLOCK_RANGE_SIZE
    first_batch_end = ((start_block // BLOCK_RANGE_SIZE) + 1) * BLOCK_RANGE_SIZE if start_block % BLOCK_RANGE_SIZE != 0 else start_block + BLOCK_RANGE_SIZE

    logger.info(f"Starting block processing from start_block={start_block} to end_block={end_block}")
    processes = []
    active_processes = []


    for current_start_block in tqdm(range(start_block, end_block, BLOCK_RANGE_SIZE), desc="Processing blocks"):
        # Calculate current end block
        if current_start_block == start_block and start_block % BLOCK_RANGE_SIZE != 0:
            current_end_block = min(first_batch_end, end_block)
        else:
            current_end_block = min(current_start_block + BLOCK_RANGE_SIZE, end_block)

        logger.info(f"Processing block range: current_start_block={current_start_block}, current_end_block={current_end_block}")
        cmd = [
            'python', os.path.join(script_dir, 'process_event_tracker.py'),
            '-n', args.contract_file,
            '-a', args.contract_address,
            '-e', args.event_file,
            '-f', str(current_start_block),
            '-t', str(current_end_block),
            '-r', args.rpc
        ]
        log_file = f"{log_dir}/job_from_{current_start_block}_to_{current_end_block}.log"
        cmd.extend(['--log-file', log_file])
        cmd.extend(['--output-file', f'{args.output_dir}/{args.output_prefix}-{args.from_block}-{args.to_block}.parquet'])
        if args.append:    
            cmd.append('-p')
        #TODO: 

        logger.info(f"Prepared command: {' '.join(cmd)}")


        # Wait if we've reached the core limit
        while len(active_processes) >= args.cores:
            # Check all active processes
            for proc in active_processes[:]:  # Create a copy to iterate over
                if proc.poll() is not None:  # Process has finished
                    active_processes.remove(proc)
            time.sleep(0.1)  # Short sleep to prevent CPU spinning

        # Start new process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_processes.append(process)
        processes.append(process)

    while active_processes:
        for proc in active_processes[:]:  # Create a copy to iterate over
            if proc.poll() is not None:
                active_processes.remove(proc)
        time.sleep(0.1)

    # Check for any errors in the completed processes
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.info(f"Process failed with return code {process.returncode}")
            logger.info(f"stderr: {stderr.decode()}")

    logger.info("All event tracking processes have completed.")

if __name__ == "__main__":
    main()
