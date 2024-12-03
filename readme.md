# Requirements


# Configuration
You have one configuration file in the `tests/` directory to pass the rpc port for the tests.

An example file is provided in `tests/env.example`.


# How to Use it

First, you need prepare a json abi contract and the solidity formatted event. Examples are provided in folders `abi` and `event`.


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
