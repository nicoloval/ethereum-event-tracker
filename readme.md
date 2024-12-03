# Requirements


# Configuration
You have one configuration file in the `tests/` directory to pass the rpc port for the tests.

An example file is provided in `tests/env.example`.


# How to Use it

First, you need to prepare a JSON ABI contract and the Solidity formatted event. Examples are provided in the folders `abi` and `event`.

## Running the Event Trackers

### parallel_event_tracker.py

This script is used to track events in parallel, dividing the work across multiple cores.

#### Usage

```bash
python sample/parallel_event_tracker.py -n <contract-file> -a <contract-address> -e <event-file> -f <from-block> -t <to-block> -c <cores> -r <rpc> -l <log-dir> -o <output-dir> -x <output-prefix>
```

#### Arguments

- `-n, --contract-file`: Path to the contract ABI file.
- `-a, --contract-address`: The address of the contract.
- `-e, --event-file`: Path to the event file.
- `-f, --from-block`: Starting block number (optional).
- `-t, --to-block`: Stopping block number (optional).
- `-c, --cores`: Number of cores to allocate to subprocesses (optional).
- `-r, --rpc`: The RPC connection string.
- `-l, --log-dir`: Path to the log directory.
- `-o, --output-dir`: Directory where the output will be stored.
- `-x, --output-prefix`: Prefix for the output files.

### process_event_tracker.py

This script processes events for a specific range of blocks.

#### Usage

```bash
python sample/process_event_tracker.py -n <contract-file> -a <contract-address> -e <event-file> -f <from-block> -t <to-block> -l <log-file> -o <output-file> -r <rpc>
```

#### Arguments

- `-n, --contract-file`: Path to the contract ABI file.
- `-a, --contract-address`: The address of the contract.
- `-e, --event-file`: Path to the event file.
- `-f, --from-block`: Starting block number (optional).
- `-t, --to-block`: Stopping block number (optional).
- `-l, --log-file`: Path to the log file.
- `-o, --output-file`: Path to the output file.
- `-r, --rpc`: The RPC connection string.


# Testing

The project includes a suite of tests to ensure the functionality of the event tracking scripts. The tests are located in the `tests` directory and are designed to verify the correct operation of the event tracking process.

## Running Tests

To run the tests, you can use a testing framework like `unittest`. Ensure that your environment is set up correctly and that the necessary dependencies are installed.

Example command to run the tests:
```
python -m unittest discover tests
```

## Environment Configuration for Tests

The tests require a `.env` file in the `tests` directory to configure the RPC URL. This file should contain the following line:

```
RPC_URL=http://localhost:8547
```

This configuration allows the test scripts to connect to a local Ethereum node running on port 8547.
You can also use third parties RPC providers as Alchemy or Infura.

# Experiments

## Transfer
## TransferShares
stETH contract
```
python parallel_event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name TransferShares --from-block 11000000
```
## TokenRebased
```
python parallel_event_tracker.py --contract-name stETH --contract-address 0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84 --event-name TokenRebased --from-block 11000000
```
